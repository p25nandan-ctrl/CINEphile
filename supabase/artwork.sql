-- Kathaa Sangam: children's artwork submissions (PROPOSAL: NOT YET RUN against a real Supabase project; run it in
-- Supabase > SQL Editor AFTER schema.sql, which defines public.is_admin()). See docs/ARTWORK_BACKEND.md.
--
-- Who can do what
--   signed-in user : upload ONE file into their own folder in the PRIVATE bucket and create a 'pending' record for it; see only their own records.
--   admin          : (auth.jwt() -> app_metadata ->> role = 'admin', set only from the Supabase dashboard) read, approve/reject, delete everything.
--   everyone else  : nothing. There is no public read of any child artwork, approved or not.

create table if not exists public.artwork_submissions (
  id               uuid primary key default gen_random_uuid(),            -- internal submission identifier
  user_id          uuid not null default auth.uid() references auth.users on delete cascade,
  story_id         text not null check (story_id ~ '^[a-z0-9-]{1,60}$'),  -- e.g. 'clever-jackal'
  storage_path     text not null unique check (storage_path ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp)$'),
  content_type     text not null check (content_type in ('image/jpeg','image/png','image/webp')),
  size_bytes       integer not null check (size_bytes between 1 and 2097152),
  title            text check (title is null or char_length(title) <= 80),
  description      text check (description is null or char_length(description) <= 300),
  consent_confirmed boolean not null check (consent_confirmed),           -- child ticked: a parent/guardian/teacher says it is OK
  status           text not null default 'pending' check (status in ('pending','approved','rejected')),
  created_at       timestamptz not null default now(),                    -- submission timestamp
  reviewed_at      timestamptz,
  reviewed_by      uuid references auth.users on delete set null
);
create index if not exists artwork_status_idx on public.artwork_submissions (status, created_at desc);
alter table public.artwork_submissions enable row level security;

create policy "child inserts own pending" on public.artwork_submissions for insert to authenticated
  with check (user_id = auth.uid() and status = 'pending' and reviewed_at is null and reviewed_by is null
              and storage_path like auth.uid()::text || '/%');
create policy "read own or admin" on public.artwork_submissions for select to authenticated
  using (user_id = auth.uid() or public.is_admin());
create policy "admin reviews" on public.artwork_submissions for update to authenticated
  using (public.is_admin()) with check (public.is_admin());
create policy "admin deletes" on public.artwork_submissions for delete to authenticated
  using (public.is_admin());
-- (no policy for anon => anonymous users can do nothing; no update policy for children => they cannot change their own status)

-- Private bucket: 2 MB, images only. Public = false means files are only reachable with a signed URL.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('child-art', 'child-art', false, 2097152, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = false, file_size_limit = 2097152, allowed_mime_types = array['image/jpeg','image/png','image/webp'];

create policy "child uploads to own folder" on storage.objects for insert to authenticated
  with check (bucket_id = 'child-art' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "read own or admin files" on storage.objects for select to authenticated
  using (bucket_id = 'child-art' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_admin()));
-- Admins can delete any file. A child can delete only a file of their own that has NO submission record (an orphan left by a failed submit).
create policy "delete orphan own or admin" on storage.objects for delete to authenticated
  using (bucket_id = 'child-art' and (public.is_admin()
         or ((storage.foldername(name))[1] = auth.uid()::text
             and not exists (select 1 from public.artwork_submissions a where a.storage_path = name))));

-- To make someone an administrator (dashboard SQL editor only; never from the website):
--   update auth.users set raw_app_meta_data = coalesce(raw_app_meta_data,'{}'::jsonb) || '{"role":"admin"}' where email = 'reviewer@example.org';
