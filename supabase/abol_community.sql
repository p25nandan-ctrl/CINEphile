-- Kathaa Sangam: Abol Tabol reader submissions (made-up creature drawings and crazy poems).
-- PROPOSAL: NOT YET RUN against a real Supabase project. Run in Supabase > SQL Editor AFTER schema.sql (defines public.is_admin()).
-- Safe to re-run: tables use IF NOT EXISTS and every policy is dropped and recreated. It only ADDS objects; it never touches an
-- existing table, row, user or bucket.
--
-- Who can do what
--   signed-in reader : create a submission (status 'pending'), see only their own, withdraw their own unless published.
--   admin            : (auth.jwt() -> app_metadata ->> role = 'admin') see everything; publish, reject, hide, delete. Never edits the
--                      child's words or picture.
--   anonymous public : read ONLY published submissions, through views that omit user_id, consent flags and every private column.
--   Nothing is published automatically: 'published' can be set only by an admin, and only if the guardian publication consent is recorded.

create or replace function public.is_admin() returns boolean language sql stable as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin'
$$;

create table if not exists public.abol_submissions (
  id                uuid primary key default gen_random_uuid(),                                  -- submission ID
  user_id           uuid not null default auth.uid() references auth.users on delete cascade,    -- authenticated author (never public)
  kind              text not null check (kind in ('creature','poem')),
  title             text not null check (char_length(btrim(title)) between 1 and 80),            -- creature name or poem title
  description       text check (description is null or char_length(description) <= 300),         -- optional short description
  body              text check (body is null or char_length(body) <= 3000),                      -- poem text (line and stanza breaks kept)
  art_path          text unique check (art_path is null or art_path ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp)$'),
  art_public_path   text unique check (art_public_path is null or art_public_path ~ '^published/[0-9a-f-]{36}\.(jpg|png|webp)$'),
  art_content_type  text check (art_content_type is null or art_content_type in ('image/jpeg','image/png','image/webp')),
  consent_confirmed boolean not null check (consent_confirmed),   -- a parent/guardian/teacher says it is OK to send this to the team
  publish_consent   boolean not null default false,               -- they ALSO say it may be shown publicly if the team approves it
  status            text not null default 'pending' check (status in ('pending','published','rejected','hidden')),
  created_at        timestamptz not null default now(),           -- submission timestamp
  reviewed_at       timestamptz,
  reviewed_by       uuid references auth.users on delete set null,
  published_at      timestamptz,
  constraint creature_needs_image check (kind <> 'creature' or art_path is not null),
  constraint poem_needs_text      check (kind <> 'poem' or char_length(btrim(coalesce(body, ''))) between 20 and 3000),
  constraint published_needs_consent check (status <> 'published' or publish_consent)
);
create index if not exists abol_sub_status_idx on public.abol_submissions (kind, status, created_at desc);
create index if not exists abol_sub_owner_idx  on public.abol_submissions (user_id, created_at desc);
alter table public.abol_submissions enable row level security;

drop policy if exists "abol insert own pending" on public.abol_submissions;
create policy "abol insert own pending" on public.abol_submissions for insert to authenticated
  with check (user_id = auth.uid() and status = 'pending' and reviewed_at is null and reviewed_by is null and published_at is null
              and art_public_path is null and (art_path is null or art_path like auth.uid()::text || '/%'));
drop policy if exists "abol read own or admin" on public.abol_submissions;
create policy "abol read own or admin" on public.abol_submissions for select to authenticated
  using (user_id = auth.uid() or public.is_admin());
drop policy if exists "abol admin moderates" on public.abol_submissions;
create policy "abol admin moderates" on public.abol_submissions for update to authenticated
  using (public.is_admin()) with check (public.is_admin());
drop policy if exists "abol withdraw or admin delete" on public.abol_submissions;
create policy "abol withdraw or admin delete" on public.abol_submissions for delete to authenticated
  using (public.is_admin() or (user_id = auth.uid() and status <> 'published'));
-- no policy for anon: anonymous visitors can do nothing on the table itself. Readers cannot update their rows at all.

-- A trigger enforces which columns an admin may change and a gentle anti-spam limit.
create or replace function public.abol_guard() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    if (select count(*) from public.abol_submissions where user_id = new.user_id and status = 'pending') >= 6 then
      raise exception 'too_many_waiting' using errcode = 'P0001';
    end if;
    return new;
  end if;
  -- UPDATE (only admins can reach here, via RLS). Admins moderate; they never rewrite a child's words, picture or consents.
  new.user_id := old.user_id; new.kind := old.kind; new.title := old.title; new.description := old.description; new.body := old.body;
  new.art_path := old.art_path; new.art_content_type := old.art_content_type; new.consent_confirmed := old.consent_confirmed;
  new.publish_consent := old.publish_consent; new.created_at := old.created_at;
  new.reviewed_at := now(); new.reviewed_by := auth.uid();
  if new.status = 'published' then new.published_at := coalesce(old.published_at, now());
  else new.published_at := null; new.art_public_path := null; end if;
  return new;
end $$;
drop trigger if exists abol_guard_trg on public.abol_submissions;
create trigger abol_guard_trg before insert or update on public.abol_submissions for each row execute function public.abol_guard();

-- Public views: published only, no user_id, no consent flags, no private path.
create or replace view public.published_abol_creatures with (security_invoker = false) as
  select id, title, description, art_public_path, published_at
  from public.abol_submissions where kind = 'creature' and status = 'published' and publish_consent;
create or replace view public.published_abol_poems with (security_invoker = false) as
  select id, title, description, body, art_public_path, published_at
  from public.abol_submissions where kind = 'poem' and status = 'published' and publish_consent;
grant select on public.published_abol_creatures, public.published_abol_poems to anon, authenticated;

-- Storage: a private bucket. Readers upload only into their own folder; an admin copies an approved picture to published/.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('abol-art', 'abol-art', false, 2097152, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = false, file_size_limit = 2097152, allowed_mime_types = array['image/jpeg','image/png','image/webp'];

create or replace function public.abol_art_is_public(p text) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.abol_submissions s where s.art_public_path = p and s.status = 'published' and s.publish_consent)
$$;
grant execute on function public.abol_art_is_public(text) to anon, authenticated;

drop policy if exists "abol reader uploads own folder" on storage.objects;
create policy "abol reader uploads own folder" on storage.objects for insert to authenticated
  with check (bucket_id = 'abol-art' and (storage.foldername(name))[1] = auth.uid()::text);
drop policy if exists "abol admin writes published copies" on storage.objects;
create policy "abol admin writes published copies" on storage.objects for insert to authenticated
  with check (bucket_id = 'abol-art' and (storage.foldername(name))[1] = 'published' and public.is_admin());
drop policy if exists "abol read own admin or published" on storage.objects;
create policy "abol read own admin or published" on storage.objects for select to anon, authenticated
  using (bucket_id = 'abol-art' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_admin() or public.abol_art_is_public(name)));
drop policy if exists "abol delete orphan own or admin" on storage.objects;
create policy "abol delete orphan own or admin" on storage.objects for delete to authenticated
  using (bucket_id = 'abol-art' and (public.is_admin()
         or ((storage.foldername(name))[1] = auth.uid()::text
             and not exists (select 1 from public.abol_submissions s where s.art_path = name))));
