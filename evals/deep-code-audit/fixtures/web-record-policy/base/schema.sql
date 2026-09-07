create table public.projects (
    id bigint primary key,
    owner_id uuid not null,
    tenant_id uuid not null,
    name text not null,
    billing_status text not null
);
alter table public.projects enable row level security;
grant select on public.projects to authenticated;
create policy member_read on public.projects for select to authenticated
using (true);
