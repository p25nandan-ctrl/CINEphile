-- Kathaa Sangam content + responses schema (PROPOSAL, NOT YET RUN OR TESTED against a real Supabase project).
-- Run in Supabase > SQL Editor. Admin = a user whose app_metadata.role = 'admin'. app_metadata can only be changed
-- from the Supabase dashboard / service role, never by the user, so it is safe to use for authorization.

create or replace function public.is_admin() returns boolean language sql stable as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin'
$$;

create table public.stories (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  title text not null,
  state_code text not null,               -- e.g. 'GJ'
  community text,                         -- only when verified
  summary text,
  cultural_context text,                  -- "About the Storytellers" body
  storyteller_refs jsonb default '[]',    -- verified references for the cultural text
  permissions_note text,                  -- licence / permission to adapt
  published boolean not null default false,
  created_at timestamptz default now(), updated_at timestamptz default now()
);
create table public.story_texts (          -- one row per language x reading level
  story_id uuid references public.stories on delete cascade,
  lang text check (lang in ('en','hi','gu','home')),
  level int check (level in (1,2,3)),     -- 1 Little Seedling, 2 Growing Sapling, 3 Mighty Tree
  body text not null, reviewed_by text,
  primary key (story_id, lang, level)
);
create table public.vocab (id uuid primary key default gen_random_uuid(), story_id uuid references public.stories on delete cascade,
  level int, word text not null, simple_en text not null, hindi text not null);
create table public.questions (id uuid primary key default gen_random_uuid(), story_id uuid references public.stories on delete cascade,
  level int, kind text, prompt text not null, sort int default 0);
create table public.sources (id uuid primary key default gen_random_uuid(), story_id uuid references public.stories on delete cascade,
  kind text check (kind in ('oral','published_retelling','adaptation','translation','illustration','ai_illustration')),
  title text, author text, publisher text, year int, url text, credit text, license text);
create table public.illustrations (id uuid primary key default gen_random_uuid(), story_id uuid references public.stories on delete cascade,
  scene text, art_style text, prompt text, storage_path text, alt_text text,
  ai_assisted boolean default true, generator text, status text default 'draft' check (status in ('draft','approved','rejected')),
  reviewed_by text, sort int default 0);
create table public.audio (story_id uuid references public.stories on delete cascade, lang text, level int, storage_path text, voice text, primary key (story_id, lang, level));

-- Children's responses: private to the signed-in user (no public read). Add parental/school consent before enabling for minors.
create table public.responses (id uuid primary key default gen_random_uuid(), user_id uuid not null default auth.uid() references auth.users on delete cascade,
  story_id uuid references public.stories, question_id uuid references public.questions, body text check (length(body) <= 4000),
  image_path text, created_at timestamptz default now());

alter table public.stories enable row level security; alter table public.story_texts enable row level security; alter table public.vocab enable row level security;
alter table public.questions enable row level security; alter table public.sources enable row level security; alter table public.illustrations enable row level security;
alter table public.audio enable row level security; alter table public.responses enable row level security;

-- Public can read only PUBLISHED stories (and their children; illustrations only when approved). Admins can do everything.
create policy "read published" on public.stories for select using (published or public.is_admin());
create policy "admin all" on public.stories for all using (public.is_admin()) with check (public.is_admin());
do $$ declare t text; begin
  foreach t in array array['story_texts','vocab','questions','sources','audio'] loop
    execute format('create policy "read if story published" on public.%I for select using (exists (select 1 from public.stories s where s.id = story_id and (s.published or public.is_admin())))', t);
    execute format('create policy "admin all" on public.%I for all using (public.is_admin()) with check (public.is_admin())', t);
  end loop; end $$;
create policy "read approved illustrations" on public.illustrations for select using ((status='approved' and exists (select 1 from public.stories s where s.id=story_id and s.published)) or public.is_admin());
create policy "admin all" on public.illustrations for all using (public.is_admin()) with check (public.is_admin());
create policy "own responses" on public.responses for all using (user_id = auth.uid()) with check (user_id = auth.uid());
-- Storage (create in dashboard): bucket "story-media" public-read for approved assets, admin-only write; bucket "child-art" PRIVATE,
-- path "{user_id}/...", policy: auth.uid()::text = (storage.foldername(name))[1]; restrict to image/png|jpeg|webp, <= 2 MB.
