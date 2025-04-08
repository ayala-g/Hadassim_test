USE ayala;

DROP TABLE IF EXISTS person;
CREATE TABLE `person` (
  `Person_Id` varchar(10) PRIMARY KEY NOT NULL,
  `Personal_Name` varchar(15) NOT NULL,
  `Family_Name` varchar(15) NOT NULL,
  `Gender` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `Father_Id` varchar(10) NOT NULL,
  `Mother_Id` varchar(10) NOT NULL,
  `Spouse_Id` varchar(10),
  UNIQUE KEY `Person_Id_UNIQUE` (`Person_Id`)
);

-- הכנסת אנשים לדוגמה לטבלת person
-- הכנסתי אנשים המוכרים לי כך שיהיה לי קל לראות את נכונות התוצאות ועבור כך גם שיניתי את התז להיות השם עם מספר כך שיבלוט לי לעין מי זה מי
INSERT INTO person (Person_Id, Personal_Name, Family_Name, Gender, Father_Id, Mother_Id, Spouse_Id) VALUES
('1אבא', 'אבא11', 'גנח', 'M', 'סבא1', 'סבתא1', '1אמא'),
('1אמא', 'אמא11', 'גנח', 'F', 'סבא2', 'סבתא2', '1אבא'),
('שמואל1', 'שמואל', 'גנח', 'M', '1אבא', '1אמא', 'מיכל1'),
('אילה1', 'אילה', 'גנח', 'F', '1אבא', '1אמא', NULL),
('יוני1', 'יוני', 'גנח', 'M', '1אבא', '1אמא', NULL),
('אוריאל1', 'אוריאל', 'גנח', 'M', '1אבא', '1אמא', NULL),
('חגית1', 'חגית', 'גנח', 'F', '1אבא', '1אמא', NULL),
('ניסים1', 'ניסים', 'גנח', 'M', '1אבא', '1אמא', NULL),
('אביגיל1', 'אביגיל', 'גנח', 'F', '1אבא', '1אמא', NULL),
('מיכל1', 'מיכל', 'גנח', 'F', 'דני', 'שרה', 'שמואל1'),
('נעמה1', 'נעמה', 'אבלסון', 'F', 'דני', 'שרה', 'אהרון');

DROP TABLE IF EXISTS fem_tree;
CREATE TABLE fem_tree (
    Person_Id VARCHAR(10),
    Relative_Id VARCHAR(10),
    Connection_Type VARCHAR(10),
    PRIMARY KEY (Person_Id, Relative_Id, Connection_Type)
);

-- תרגיל 1: פרוצדורה להוספת קשרים משפחתיים בסיסיים
-- מוסיפים את הקשרים: אב, אם, בן, בת, בן זוג, בת זוג (חד כיווני)
DROP PROCEDURE IF EXISTS add_family_relationships;
DELIMITER $$
CREATE PROCEDURE add_family_relationships()
BEGIN
    -- הוספת קשר אב לכל אחד
    INSERT INTO fem_tree (Person_Id, Relative_Id, Connection_Type)
    SELECT p.Person_Id, p.Father_Id, 'אבא'
    FROM person p
    WHERE p.Father_Id IS NOT NULL AND p.Father_Id <> ''
    AND NOT EXISTS (
        SELECT 1 FROM fem_tree ft 
        WHERE ft.Person_Id = p.Person_Id 
          AND ft.Relative_Id = p.Father_Id 
          AND ft.Connection_Type = 'אבא'
    );

    -- הוספת קשר אם לכל אחד
    INSERT INTO fem_tree (Person_Id, Relative_Id, Connection_Type)
    SELECT p.Person_Id, p.Mother_Id, 'אמא'
    FROM person p
    WHERE p.Mother_Id IS NOT NULL AND p.Mother_Id <> ''
    AND NOT EXISTS (
        SELECT 1 FROM fem_tree ft 
        WHERE ft.Person_Id = p.Person_Id 
          AND ft.Relative_Id = p.Mother_Id 
          AND ft.Connection_Type = 'אמא'
    );

    -- הוספת קשר בן/בת זוג - לפי מין
    INSERT INTO fem_tree (Person_Id, Relative_Id, Connection_Type)
    SELECT p.Person_Id, p.Spouse_Id, 
           CASE 
               WHEN p.Gender = 'M' THEN 'בת זוג' 
               WHEN p.Gender = 'F' THEN 'בן זוג' 
           END 
    FROM person p
    WHERE p.Spouse_Id IS NOT NULL AND p.Spouse_Id <> ''
    AND NOT EXISTS (
        SELECT 1 FROM fem_tree ft 
        WHERE ft.Person_Id = p.Person_Id 
          AND ft.Relative_Id = p.Spouse_Id 
          AND ft.Connection_Type IN ('בן זוג', 'בת זוג')
    );

    -- הוספת קשר בן/בת מהאב
    INSERT INTO fem_tree (Person_Id, Relative_Id, Connection_Type)
    SELECT p.Father_Id, p.Person_Id, 
           CASE 
               WHEN p.Gender = 'M' THEN 'בן' 
               WHEN p.Gender = 'F' THEN 'בת' 
           END 
    FROM person p
    WHERE p.Father_Id IS NOT NULL AND p.Father_Id <> ''
    AND NOT EXISTS (
        SELECT 1 FROM fem_tree ft 
        WHERE ft.Person_Id = p.Father_Id 
          AND ft.Relative_Id = p.Person_Id 
          AND ft.Connection_Type IN ('בן', 'בת')
    );

    -- הוספת קשר בן/בת מהאם
    INSERT INTO fem_tree (Person_Id, Relative_Id, Connection_Type)
    SELECT p.Mother_Id, p.Person_Id, 
           CASE 
               WHEN p.Gender = 'M' THEN 'בן' 
               WHEN p.Gender = 'F' THEN 'בת' 
           END 
    FROM person p
    WHERE p.Mother_Id IS NOT NULL AND p.Mother_Id <> ''
    AND NOT EXISTS (
        SELECT 1 FROM fem_tree ft 
        WHERE ft.Person_Id = p.Mother_Id 
          AND ft.Relative_Id = p.Person_Id 
          AND ft.Connection_Type IN ('בן', 'בת')
    );
END $$
DELIMITER ;

-- תרגיל 1 (המשך): פרוצדורה שמוסיפה קשרים בין אחים ואחיות
DROP PROCEDURE IF EXISTS add_sibling_relationships;
DELIMITER $$
CREATE PROCEDURE add_sibling_relationships()
BEGIN
    -- לכל זוג אחים (אותם הורים), מוסיפים קשרי אח/אחות בהתאם למגדר
    INSERT INTO fem_tree (Person_Id, Relative_Id, Connection_Type)
    SELECT 
        p1.Person_Id,
        p2.Person_Id,
        CASE WHEN p2.Gender = 'M' THEN 'אח' ELSE 'אחות' END
    FROM person p1
    JOIN person p2
      ON p1.Father_Id = p2.Father_Id AND p1.Mother_Id = p2.Mother_Id
    WHERE p1.Person_Id <> p2.Person_Id
      AND NOT EXISTS (
        SELECT 1 FROM fem_tree f
        WHERE f.Person_Id = p1.Person_Id 
          AND f.Relative_Id = p2.Person_Id
          AND f.Connection_Type IN ('אח', 'אחות')
    );
END $$
DELIMITER ;

-- תרגיל 2: השלמת קשרי בני זוג (כיוון הפוך)
DROP PROCEDURE IF EXISTS complete_spouse_relationships;
DELIMITER $$
CREATE PROCEDURE complete_spouse_relationships()
BEGIN
    -- מוסיפים קשר הפוך - אם אדם X מקושר ל-Y כבן זוג, מוסיפים גם ל-Y קשר הפוך
    INSERT INTO fem_tree (Person_Id, Relative_Id, Connection_Type)
    SELECT
        ft.Relative_Id,
        ft.Person_Id,
        CASE 
            WHEN ft.Connection_Type = 'בן זוג' THEN 'בת זוג'
            WHEN ft.Connection_Type = 'בת זוג' THEN 'בן זוג'
        END
    FROM fem_tree ft
    WHERE ft.Connection_Type IN ('בן זוג', 'בת זוג')
      AND NOT EXISTS (
          SELECT 1 
          FROM fem_tree f2
          WHERE f2.Person_Id = ft.Relative_Id
            AND f2.Relative_Id = ft.Person_Id
            AND (
                (ft.Connection_Type = 'בן זוג' AND f2.Connection_Type = 'בת זוג') OR
                (ft.Connection_Type = 'בת זוג' AND f2.Connection_Type = 'בן זוג')
            )
      );
END $$
DELIMITER ;

-- הפעלת כל הפרוצדורות כדי למלא את עץ המשפחה
CALL add_family_relationships();
CALL add_sibling_relationships();
CALL complete_spouse_relationships();

-- הצגת כל הקשרים המשפחתיים שנוצרו
SELECT * FROM fem_tree ORDER BY Person_Id, Connection_Type;
