create table
    public.capacity (
        id int8 key not null generated,
        timestamp timestampz not null now(),
        ml_capacity int4,
        potion_capacity int4
    )

check jpg