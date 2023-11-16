INSERT INTO score (date, user_id, score)
    SELECT date, 1 as user_id, will_score AS score
    FROM day
    WHERE will_score IS NOT NULL
    UNION
    SELECT date, 2 as user_id, kate_score AS score
    FROM day
    WHERE kate_score IS NOT NULL
