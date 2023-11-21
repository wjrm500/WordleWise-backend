UPDATE user 
SET forename = CASE 
        WHEN id = 1 THEN 'Will' 
        WHEN id = 2 THEN 'Kate' 
    END 
WHERE id IN (1, 2);
