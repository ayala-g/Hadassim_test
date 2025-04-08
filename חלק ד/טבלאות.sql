USE ayala;

-- מחיקת הטבלאות הקיימות במקרה שכבר קיימות (סדר חשוב כי יש קשרים ביניהן)
DROP TABLE IF EXISTS Order_Items;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Products;
DROP TABLE IF EXISTS Suppliers;
-- טבלת הספקים: שומרת מידע על כל ספק לפי שם החברה שלו, שהוא מזהה ייחודי.
-- בהנחה ששם החברה הוא ייחודי ומשמש לזיהוי ספקים שונים כך כל ספק הוא בעצם חברה נפרדת עם שם שונה, ולכן company_name הוא המפתח הראשי.
CREATE TABLE Suppliers (
    company_name VARCHAR(15) PRIMARY KEY NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    representative_name VARCHAR(15) NOT NULL
);

-- טבלת המוצרים: שומרת מידע על כל מוצר שהספקים מציעים.
-- בהנחה ששם המוצר הוא ייחודי, ולכן משמש כמזהה ראשי (Primary Key) של המוצר.
CREATE TABLE Products (
    product_name VARCHAR(15) NOT NULL,
    price DECIMAL(10, 2) NOT NULL, -- מחיר עם 2 ספרות אחרי הנקודה
    min_quantity INT NOT NULL,
    supplier_name VARCHAR(15),
    PRIMARY KEY (product_name, supplier_name),
    FOREIGN KEY (supplier_name) REFERENCES Suppliers(company_name)
);

-- טבלת ההזמנות: שומרת את ההזמנות שבעל המכולת ביצע/מבצע מהספקים.
-- היא אומרת: הערך של supplier_name בטבלה Orders חייב להתאים לערך קיים של company_name בטבלה Suppliers. זה מקשר בין הטבלאות – כך שכל הזמנה תהיה שייכת לספק קיים.
CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(15) NOT NULL,
    status ENUM('ממתינה', 'בתהליך', 'הושלמה') NOT NULL,
    seen_by_supplier BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (supplier_name) REFERENCES Suppliers(company_name)
);

-- טבלת פרטי ההזמנה: שומרת אילו מוצרים יש בכל הזמנה וכמה
-- מזהה כל שורה לפי שילוב של מספר הזמנה ושם מוצר, כי יכול להיות שבאותה הזמנה יהיו כמה מוצרים וכל מוצר יופיע רק פעם אחת להזמנה והשילוב ביניהם הוא מה שמאפיין את אותה השורה - מוצר מסוים בהזמנה מסוימת.
CREATE TABLE Order_Items (
    order_id INT NOT NULL,
    product_name VARCHAR(15) NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (order_id, product_name),
    -- הערך של order_id כאן חייב להתאים לערך קיים של order_id בטבלה Orders כך שכל רשומת מוצר כאן חייבת להשתייך להזמנה קיימת.
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    -- הערך של product_name כאן חייב להיות קיים בטבלה Products כך שלא תהיה אפשרות להכניס מוצר שלא מוגדר ברשימת המוצרים
    FOREIGN KEY (product_name) REFERENCES Products(product_name)
);

DROP TABLE IF EXISTS inventory;
CREATE TABLE inventory (
    product_name VARCHAR(15) PRIMARY KEY,
    current_quantity INT NOT NULL,
    min_required INT NOT NULL
);

