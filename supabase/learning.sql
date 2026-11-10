-- Kathaa Sangam: personalised learning (child profiles, consent, progress, written answers, quiz evidence, reviews)
-- Run in Supabase > SQL Editor. Safe to run once on a project that has NOT yet run schema.sql / artwork.sql; if it has, this file only
-- adds new tables and one nullable column. It never drops or overwrites existing tables, stories or users.
-- STATUS: written for review. It has NOT been run against a real Supabase project. See docs/LEARNING_SETUP_AND_TESTS.md.
--
-- Account model (parent / teacher accounts):
--   auth.users row  = an ADULT (parent, guardian or teacher). Their email is the only contact detail we hold.
--   child_profiles  = a nickname + grade + reading level created by that adult. No child email, real name, school or address.
--   Every learning table hangs off child_profiles.id, and every policy checks the child belongs to auth.uid().

create or replace function public.is_admin() returns boolean language sql stable as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin'
$$;

-- 1. Consent record kept for the adult account (what they agreed to, which version of the text, when).
create table if not exists public.consent_records (
  id          uuid primary key default gen_random_uuid(),
  guardian_id uuid not null default auth.uid() references auth.users on delete cascade,
  version     text not null check (char_length(version) between 1 and 20),
  role        text not null check (role in ('parent','guardian','teacher')),
  accepted_at timestamptz not null default now(),
  unique (guardian_id, version)
);

-- 2. Child profiles (minimal data).
create table if not exists public.child_profiles (
  id          uuid primary key default gen_random_uuid(),
  guardian_id uuid not null default auth.uid() references auth.users on delete cascade,
  nickname    text not null check (char_length(nickname) between 1 and 24),
  grade       smallint check (grade is null or grade between 1 and 12),
  level       smallint not null default 1 check (level between 1 and 3),   -- 1 Little Seedling, 2 Growing Sapling, 3 Mighty Tree
  created_at  timestamptz not null default now()
);
create index if not exists child_profiles_guardian_idx on public.child_profiles (guardian_id);

create or replace function public.owns_child(cid uuid) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.child_profiles c where c.id = cid and c.guardian_id = auth.uid())
$$;

-- A guardian may have at most 8 child profiles.
create or replace function public.limit_children() returns trigger language plpgsql as $$
begin
  if (select count(*) from public.child_profiles where guardian_id = new.guardian_id) >= 8 then
    raise exception 'too many child profiles' using errcode = 'check_violation';
  end if;
  return new;
end $$;
drop trigger if exists limit_children_t on public.child_profiles;
create trigger limit_children_t before insert on public.child_profiles for each row execute function public.limit_children();

-- 3. Reading progress: one row per child x story x reading level.
create table if not exists public.story_progress (
  child_id     uuid not null references public.child_profiles on delete cascade,
  story_id     text not null check (story_id ~ '^[a-z0-9-]{1,60}$'),
  level        smallint not null check (level between 1 and 3),
  status       text not null default 'reading' check (status in ('reading','completed')),
  page         smallint not null default 0 check (page between -1 and 60),   -- last spread reached (-1 = cover)
  started_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),   -- last-read timestamp
  completed_at timestamptz,
  primary key (child_id, story_id, level)
);

-- 4. Written answers to Think / Imagine / Create.
create table if not exists public.child_responses (
  id          uuid primary key default gen_random_uuid(),
  child_id    uuid not null references public.child_profiles on delete cascade,
  story_id    text not null check (story_id ~ '^[a-z0-9-]{1,60}$'),
  level       smallint not null check (level between 1 and 3),
  question_id text not null check (question_id ~ '^[0-9IC]{1,3}$'),
  body        text not null check (char_length(body) between 1 and 3000),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (child_id, story_id, level, question_id)
);

-- 5. Auto-checked quiz evidence. Append-only: every attempt is kept; the app scores the FIRST attempt at each item.
--    Limitation (stated honestly): answer keys ship with the page, so correctness is reported by the browser. A child could
--    alter their own results. Nobody else is affected. These scores are formative guidance, not a test.
create table if not exists public.quiz_attempts (
  id         uuid primary key default gen_random_uuid(),
  child_id   uuid not null references public.child_profiles on delete cascade,
  story_id   text not null check (story_id ~ '^[a-z0-9-]{1,60}$'),
  level      smallint not null check (level between 1 and 3),
  item_id    text not null check (item_id ~ '^[a-z0-9._-]{1,80}$'),
  dimension  text not null check (dimension in ('comprehension','vocabulary')),
  chosen     smallint not null check (chosen between 0 and 5),
  correct    boolean not null,
  created_at timestamptz not null default now()
);
create index if not exists quiz_attempts_child_idx on public.quiz_attempts (child_id, created_at);

-- 6. Reviewer scores for the two dimensions a computer cannot judge reliably (written expression, critical thinking).
create table if not exists public.response_reviews (
  response_id uuid primary key references public.child_responses on delete cascade,
  reviewer    uuid references auth.users on delete set null default auth.uid(),
  written     smallint not null check (written between 0 and 4),
  critical    smallint not null check (critical between 0 and 4),
  note        text check (note is null or char_length(note) <= 500),
  reviewed_at timestamptz not null default now()
);

-- 7. Link artwork to the child profile it belongs to (nullable; existing rows untouched).
do $$ begin
  if to_regclass('public.artwork_submissions') is not null then
    alter table public.artwork_submissions add column if not exists child_id uuid references public.child_profiles on delete set null;
  end if;
end $$;

-- ---------- Row Level Security ----------
alter table public.consent_records  enable row level security;
alter table public.child_profiles   enable row level security;
alter table public.story_progress   enable row level security;
alter table public.child_responses  enable row level security;
alter table public.quiz_attempts    enable row level security;
alter table public.response_reviews enable row level security;

create policy "own consent read"   on public.consent_records for select to authenticated using (guardian_id = auth.uid());
create policy "own consent insert" on public.consent_records for insert to authenticated with check (guardian_id = auth.uid());

create policy "own children read"   on public.child_profiles for select to authenticated using (guardian_id = auth.uid() or public.is_admin());
create policy "own children insert" on public.child_profiles for insert to authenticated with check (guardian_id = auth.uid());
create policy "own children update" on public.child_profiles for update to authenticated using (guardian_id = auth.uid()) with check (guardian_id = auth.uid());
create policy "own children delete" on public.child_profiles for delete to authenticated using (guardian_id = auth.uid());

create policy "progress read"   on public.story_progress for select to authenticated using (public.owns_child(child_id));
create policy "progress insert" on public.story_progress for insert to authenticated with check (public.owns_child(child_id));
create policy "progress update" on public.story_progress for update to authenticated using (public.owns_child(child_id)) with check (public.owns_child(child_id));

create policy "answers read"   on public.child_responses for select to authenticated using (public.owns_child(child_id) or public.is_admin());
create policy "answers insert" on public.child_responses for insert to authenticated with check (public.owns_child(child_id));
create policy "answers update" on public.child_responses for update to authenticated using (public.owns_child(child_id)) with check (public.owns_child(child_id));
create policy "answers delete" on public.child_responses for delete to authenticated using (public.owns_child(child_id));

create policy "quiz read"   on public.quiz_attempts for select to authenticated using (public.owns_child(child_id));
create policy "quiz insert" on public.quiz_attempts for insert to authenticated with check (public.owns_child(child_id));
-- no update / delete policy for quiz_attempts: evidence cannot be rewritten (it is removed only when a child profile is deleted).

create policy "reviews read"   on public.response_reviews for select to authenticated
  using (public.is_admin() or exists (select 1 from public.child_responses r where r.id = response_id and public.owns_child(r.child_id)));
create policy "reviews admin insert" on public.response_reviews for insert to authenticated with check (public.is_admin());
create policy "reviews admin update" on public.response_reviews for update to authenticated using (public.is_admin()) with check (public.is_admin());
create policy "reviews admin delete" on public.response_reviews for delete to authenticated using (public.is_admin());

-- Replace the insert policy on artwork (artwork.sql) so child_id, when given, must belong to the signed-in adult.
do $$ begin
  if to_regclass('public.artwork_submissions') is not null then
    drop policy if exists "child inserts own pending" on public.artwork_submissions;
    create policy "child inserts own pending" on public.artwork_submissions for insert to authenticated
      with check (user_id = auth.uid() and status = 'pending' and reviewed_at is null and reviewed_by is null
                  and storage_path like auth.uid()::text || '/%'
                  and (child_id is null or public.owns_child(child_id)));
  end if;
end $$;

-- ---------- Deleting a child's data ----------
-- The adult uses "Delete this profile" in the app (delete from child_profiles where id = ...). ON DELETE CASCADE removes that
-- child's progress, answers, quiz attempts and reviews. Artwork the child sent stays under the adult's account (child_id becomes null)
-- until an administrator deletes it; ask the project team to remove artwork on request.
