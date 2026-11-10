-- Kathaa Sangam: "Share Your Story" (reader submissions) and "Voices From Our Readers" (testimonials).
-- PROPOSAL: NOT YET RUN against a real Supabase project. Run it in Supabase > SQL Editor AFTER schema.sql (which defines
-- public.is_admin()) and AFTER artwork.sql. It only ADDS objects; it does not touch any existing table, row or bucket.
-- See docs/COMMUNITY_SETUP_AND_TESTS.md.
--
-- Who can do what
--   signed-in reader : create a story (status 'pending'), see only their own stories and their status, edit a story that is
--                      'pending' or has a 'revision_requested' note, withdraw (delete) their own story unless it is published.
--   admin            : (auth.jwt() -> app_metadata ->> role = 'admin', set only from the Supabase dashboard) see everything, change
--                      ONLY the moderation fields (status, note, publish state), never the child's words. Delete anything.
--   anonymous public : read ONLY stories whose status is 'published' (and whose author gave publish consent), through a view that
--                      leaves out user_id and every private column; read ONLY testimonials whose status is 'approved'.
--   Nothing is ever published automatically: 'published' can be set only by an admin.

/* ======================= reader stories ======================= */
create table if not exists public.user_stories (
  id                uuid primary key default gen_random_uuid(),                                   -- submission ID
  user_id           uuid not null default auth.uid() references auth.users on delete cascade,     -- authenticated author (never shown publicly)
  title             text not null check (char_length(btrim(title)) between 1 and 100),
  body              text not null check (char_length(btrim(body)) between 20 and 8000),
  language          text not null check (language in ('en','hi')),
  state_id          text check (state_id is null or state_id in (                                  -- optional; only India's 28 states
                      'as','kl','mh','gj','ap','ar','br','ct','ga','hr','hp','jh','ka','mp','mn','ml','mz','nl','or','pb','rj','sk','tn','tg','tr','up','ut','wb')),
  inspiration       text check (inspiration is null or char_length(inspiration) <= 300),
  art_path          text unique check (art_path is null or art_path ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp)$'),
  art_content_type  text check (art_content_type is null or art_content_type in ('image/jpeg','image/png','image/webp')),
  art_public_path   text unique check (art_public_path is null or art_public_path ~ '^published/[0-9a-f-]{36}\.(jpg|png|webp)$'), -- copy made by an admin when publishing
  consent_confirmed boolean not null check (consent_confirmed),                                    -- a parent/guardian/teacher says it is OK to send this to the team
  publish_consent   boolean not null default false,                                                -- a parent/guardian/teacher ALSO says it may be shown publicly if approved
  status            text not null default 'pending' check (status in ('pending','revision_requested','approved','published','rejected')),
  admin_note        text check (admin_note is null or char_length(admin_note) <= 500),             -- shown to the author, e.g. what to change
  created_at        timestamptz not null default now(),                                           -- submission timestamp
  updated_at        timestamptz not null default now(),
  reviewed_at       timestamptz,
  reviewed_by       uuid references auth.users on delete set null,
  published_at      timestamptz,
  constraint published_needs_consent check (status <> 'published' or publish_consent)
);
create index if not exists user_stories_status_idx on public.user_stories (status, created_at desc);
create index if not exists user_stories_owner_idx  on public.user_stories (user_id, created_at desc);
alter table public.user_stories enable row level security;

create policy "reader inserts own pending story" on public.user_stories for insert to authenticated
  with check (user_id = auth.uid() and status = 'pending' and reviewed_at is null and reviewed_by is null and published_at is null
              and admin_note is null and art_public_path is null
              and (art_path is null or art_path like auth.uid()::text || '/%'));
create policy "read own or admin" on public.user_stories for select to authenticated
  using (user_id = auth.uid() or public.is_admin());
create policy "owner edits own" on public.user_stories for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "admin moderates" on public.user_stories for update to authenticated
  using (public.is_admin()) with check (public.is_admin());
create policy "owner withdraws unpublished or admin deletes" on public.user_stories for delete to authenticated
  using (public.is_admin() or (user_id = auth.uid() and status <> 'published'));
-- no policy for anon => anonymous users can do nothing on the table itself

-- One trigger enforces which columns each kind of caller may change (RLS alone cannot do column rules).
create or replace function public.user_stories_guard() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    if (select count(*) from public.user_stories where user_id = new.user_id and status in ('pending','revision_requested')) >= 5 then
      raise exception 'too_many_waiting' using errcode = 'P0001';             -- gentle anti-spam: at most 5 stories waiting at once
    end if;
    new.updated_at := now();
    return new;
  end if;
  if public.is_admin() then
    -- an admin moderates; they never rewrite a child's words, change the author or the consents
    new.user_id := old.user_id; new.title := old.title; new.body := old.body; new.language := old.language; new.state_id := old.state_id;
    new.inspiration := old.inspiration; new.art_path := old.art_path; new.art_content_type := old.art_content_type;
    new.consent_confirmed := old.consent_confirmed; new.publish_consent := old.publish_consent; new.created_at := old.created_at;
    new.reviewed_at := now(); new.reviewed_by := auth.uid();
    if new.status = 'published' then new.published_at := coalesce(old.published_at, now());
    else new.published_at := null; new.art_public_path := null; end if;
  else
    if old.status not in ('pending','revision_requested') then raise exception 'locked' using errcode = 'P0001'; end if;
    new.user_id := old.user_id; new.status := 'pending';                      -- editing sends it back for review
    new.admin_note := old.admin_note; new.reviewed_at := old.reviewed_at; new.reviewed_by := old.reviewed_by;
    new.published_at := null; new.art_public_path := null; new.created_at := old.created_at;
  end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists user_stories_guard_trg on public.user_stories;
create trigger user_stories_guard_trg before insert or update on public.user_stories for each row execute function public.user_stories_guard();

-- What the public may read: published stories only, WITHOUT user_id, notes or review data.
create or replace view public.published_user_stories with (security_invoker = false) as
  select id, title, body, language, state_id, inspiration, art_public_path, published_at
  from public.user_stories where status = 'published' and publish_consent;
grant select on public.published_user_stories to anon, authenticated;

/* ======================= storage for story pictures ======================= */
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('story-art', 'story-art', false, 2097152, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = false, file_size_limit = 2097152, allowed_mime_types = array['image/jpeg','image/png','image/webp'];

create or replace function public.story_art_is_public(p text) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.user_stories s where s.art_public_path = p and s.status = 'published' and s.publish_consent)
$$;
grant execute on function public.story_art_is_public(text) to anon, authenticated;

create policy "reader uploads to own folder" on storage.objects for insert to authenticated
  with check (bucket_id = 'story-art' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "admin writes published copies" on storage.objects for insert to authenticated
  with check (bucket_id = 'story-art' and (storage.foldername(name))[1] = 'published' and public.is_admin());
create policy "read own, admin, or published copy" on storage.objects for select to anon, authenticated
  using (bucket_id = 'story-art' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_admin() or public.story_art_is_public(name)));
create policy "delete orphan own or admin" on storage.objects for delete to authenticated
  using (bucket_id = 'story-art' and (public.is_admin()
         or ((storage.foldername(name))[1] = auth.uid()::text
             and not exists (select 1 from public.user_stories s where s.art_path = name))));

/* ======================= testimonials ======================= */
-- Only administrators write here. There is NO public submission form: a testimonial exists only because a person genuinely gave
-- the feedback and an administrator recorded where it came from. Nothing is shown until an admin sets status = 'approved'.
create table if not exists public.testimonials (
  id                   uuid primary key default gen_random_uuid(),
  quote                text not null check (char_length(btrim(quote)) between 10 and 400),
  role                 text not null check (role in ('student','teacher','parent','educator','other')),
  display_name         text check (display_name is null or char_length(display_name) <= 60),   -- optional, only as approved by the person
  is_child             boolean not null default false,                                          -- the words are a child's
  permission_confirmed boolean not null default false,                                          -- parent/guardian/teacher permission for public display
  source_note          text check (source_note is null or char_length(source_note) <= 300),     -- PRIVATE: how/when the feedback was received
  status               text not null default 'draft' check (status in ('draft','approved','hidden')),
  sort_order           integer not null default 0,
  created_by           uuid default auth.uid() references auth.users on delete set null,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),
  constraint child_needs_permission check (status <> 'approved' or not is_child or permission_confirmed),
  constraint approved_needs_source  check (status <> 'approved' or char_length(btrim(coalesce(source_note, ''))) > 0)
);
alter table public.testimonials enable row level security;
create policy "admin manages testimonials" on public.testimonials for all to authenticated
  using (public.is_admin()) with check (public.is_admin());
create or replace view public.published_testimonials with (security_invoker = false) as
  select id, quote, role, display_name, sort_order from public.testimonials where status = 'approved';
grant select on public.published_testimonials to anon, authenticated;

-- To make someone an administrator (dashboard SQL editor only; never from the website):
--   update auth.users set raw_app_meta_data = coalesce(raw_app_meta_data,'{}'::jsonb) || '{"role":"admin"}' where email = 'reviewer@example.org';
