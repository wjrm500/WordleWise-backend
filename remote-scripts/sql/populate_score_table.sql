INSERT INTO score
    SELECT date, 1 as user_id, will_score AS score
    FROM day
    UNION
    SELECT date, 2 as user_id, kate_score AS score
    FROM day
