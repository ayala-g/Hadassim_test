from flask import Flask, request, jsonify
import mysql.connector

# יצירת אפליקציה של Flask
app = Flask(__name__)

# פונקציה שמבצעת את החיבור למסד הנתונים שלנו (MySQL)
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",       
        user="root",           
        password="ayala",     
        database="ayala"      
    )
    return connection

# התחברות או רישום של ספק חדש (עבור צד הספק)
@app.route('/login_or_register_supplier', methods=['POST'])
def login_or_register_supplier():
    data = request.get_json()
    company_name = data.get('company_name')

    # בדיקה שחייב להיות שם חברה
    if not company_name:
        return jsonify({'error': 'יש להזין שם חברה'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # בודק אם הספק כבר קיים במערכת
        cursor.execute("SELECT * FROM Suppliers WHERE company_name = %s", (company_name,))
        supplier = cursor.fetchone()

        if supplier:
            # אם קיים נחזיר אישור התחברות
            return jsonify({'message': 'התחברות הצליחה', 'supplier_name': company_name}), 200
        else:
            # אם לא קיים נבקש גם פרטי יצירת קשר וסחורה להרשמה של הספק החדש
            phone = data.get('phone_number')
            contact_name = data.get('representative_name')
            products = data.get('products', [])

            if not phone or not contact_name or not products:
                return jsonify({'error': 'חסרים פרטים לרישום ספק חדש'}), 400

            # מוסיף את הספק לטבלת הספקים
            cursor.execute("""
                INSERT INTO Suppliers (company_name, phone_number, representative_name)
                VALUES (%s, %s, %s)
            """, (company_name, phone, contact_name))

            # מוסיף את כל הסחורות של הספק החדש
            for product in products:
                cursor.execute("""
                    INSERT INTO Products (product_name, supplier_name, price, min_quantity)
                    VALUES (%s, %s, %s, %s)
                """, (
                    product['product_name'],
                    company_name,
                    product['price'],
                    product['min_quantity']
                ))

            conn.commit()
            return jsonify({'message': 'הספק נרשם בהצלחה', 'supplier_name': company_name}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

#פונקציה הבודקת זמינות של מוצר ואשר בודקת אם הנתונים בהזמנה תואמים לדרישות המוצר
# (הכמות חוקית, אם המוצר קיים אצל הספק, ואם עומד בכמות המינימלית)
def validate_order_item(product_name, quantity, company_name, cursor):
    # נבדוק שלא חסר שם מוצר או כמות
    if not product_name or quantity is None:
        return False, "פריט לא תקין: חסר שם מוצר או כמות"

    # נהפוך את הכמות לסוג מספר שלם
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return False, f"הכמות עבור '{product_name}' לא נראית כמו מספר תקין"

    # בודקים שהכמות היא חיובית (אי אפשר להזמין 0 או פחות)
    if quantity <= 0:
        return False, f"הכמות עבור '{product_name}' חייבת להיות מספר חיובי"

    #נבדוק בבסיס הנתונים אם המוצר קיים אצל הספק הספציפי
    cursor.execute(
        "SELECT * FROM Products WHERE product_name = %s AND supplier_name = %s",
        (product_name, company_name)
    )
    product = cursor.fetchone()

    # אם לא קיים נחזיר הודעת שגיאה
    if not product:
        return False, f"המוצר '{product_name}' לא מופיע אצל הספק '{company_name}'"

    # בודקים אם הכמות שביקשו עומדת במינימום של המוצר
    if quantity < product["min_quantity"]:
        return False, f"הכמות עבור '{product_name}' נמוכה מהמינימום ({product['min_quantity']})"

    # אם הכל בסדר, נחזיר את הפריט 
    return True, {"product_name": product_name, "quantity": quantity}

# הפונקצייה יוצרת הזמנה חדשה לספק מסויים
# מקבלת את שם הספק, רשימת מוצרים וחיבור למסד הנתונים
def create_order_for_supplier(company_name, items, conn):
    cursor = conn.cursor(dictionary=True)

    # נוודא שהספק באמת קיים במערכת
    cursor.execute("SELECT * FROM suppliers WHERE company_name = %s", (company_name,))
    supplier_row = cursor.fetchone()
    if not supplier_row:
        return {'error': 'הספק לא קיים במערכת'}, 400

    approved_items = []   # כאן נכניס פריטים תקינים להזמנה
    skipped = []          # כאן נשמור את מה שלא תקין עם הסבר

    for item in items:
        name = item.get("product_name")
        qty = item.get("quantity")

        # בודקים שהפריט תקין (כמות, קיום אצל הספק וכו’)
        valid, check = validate_order_item(name, qty, company_name, cursor)

        if not valid:
            skipped.append(check)
            continue

        approved_items.append((name, int(qty)))

    # אם אף מוצר לא עבר תקין לא ניצור הזמנה
    if not approved_items:
        return {
            'error': 'כל המוצרים נפסלו. אין מה להזמין.',
            'details': skipped
        }, 400

    # ניצור שורה חדשה בטבלת ההזמנות (עם הסטטוס התחלתי: ממתינה)
    cursor.execute("""
        INSERT INTO orders (supplier_name, status) 
        VALUES (%s, %s)
    """, (company_name, "ממתינה"))
    
    order_id = cursor.lastrowid  # נשמור את ה id של ההזמנה

    # נוסיף את כל המוצרים התקינים להזמנה
    for name, qty in approved_items:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_name, quantity)
            VALUES (%s, %s, %s)
        """, (order_id, name, qty))

    # את שמירת השינויים נשמור מחוץ לפונקצייה, איפה שנקרא לה.

    return {
        'message': 'ההזמנה נשמרה בהצלחה.',
        'order_id': order_id,
        'ignored_items': skipped
    }, 201

#יצירת הזמנה חדשה (ע"י בעל המכולת)
@app.route("/create_order", methods=["POST"])
def create_order():
    data = request.get_json()
    company_name = data.get("company_name")
    items = data.get("items")

    # אם לא נשלחו כל הנתונים  נחזיר שגיאה
    if not company_name or not items:
        return jsonify({"error": "יש לספק שם ספק ופריטי הזמנה"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # יוצרים את ההזמנה בפועל
        response, status_code = create_order_for_supplier(company_name, items, conn)

        if status_code == 201:
            conn.commit()  # אם ההזמנה הצליחה נשמור את הכל 
        else:
            conn.rollback()  # אם לא הצליח נבטל את  השינויים

        return jsonify(response), status_code

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

#  (עבור צד הספק)צפייה בהזמנות בעל המכולת לפי ספק
@app.route('/supplier_orders', methods=['GET'])
def get_supplier_orders():
    company_name = request.args.get('company_name')

    # אם לא נשלח שם ספק נחזיר שגיאה
    if not company_name:
        return jsonify({'error': 'חסר שם ספק'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # נקח את כל ההזמנות של הספק מהטבלה
        cursor.execute("SELECT * FROM Orders WHERE supplier_name = %s", (company_name,))
        orders = cursor.fetchall()

        return jsonify({'orders': orders}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# צפייה בפריטים של הזמנה מסוימת של ספק (עבור צד הספק)
@app.route('/order_items', methods=['GET'])
def get_order_items():
    order_id = request.args.get('order_id')
    company_name = request.args.get('company_name')  # נוודא את שם הספק

    # נבדוק שיש את כל המידע הדרוש
    if not order_id or not company_name:
        return jsonify({'error': 'חסר מזהה הזמנה או שם ספק'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # נבדוק שההזמנה אכן שייכת לספק הזה
        cursor.execute("""
            SELECT * FROM Orders 
            WHERE order_id = %s AND supplier_name = %s
        """, (order_id, company_name))
        order = cursor.fetchone()

        if not order:
            return jsonify({'error': 'ההזמנה לא קיימת או לא שייכת לספק'}), 403

        # נקח את הפריטים של ההזמנה
        cursor.execute("""
            SELECT product_name, quantity 
            FROM Order_Items 
            WHERE order_id = %s
        """, (order_id,))
        items = cursor.fetchall()

        if not items:
            return jsonify({'message': 'אין פריטים להזמנה הזו'}), 404

        # נחזיר את הסטטוס של ההזמנה וגם את הפריטים
        return jsonify({
            'status': order['status'],
            'items': items
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# אישור הזמנה – מעדכן סטטוס ההזמנה ל"בתהליך" (עבור צד הספק)
@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    data = request.get_json()
    order_id = data.get('order_id')
    company_name = data.get('company_name')

    # נבדוק שיש את כל הנתונים הדרושים
    if not order_id or not company_name:
        return jsonify({'error': 'חסר מזהה הזמנה או שם ספק'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # נבדוק שההזמנה באמת שייכת לספק הזה
        cursor.execute("""
            SELECT * FROM Orders 
            WHERE order_id = %s AND supplier_name = %s
        """, (order_id, company_name))
        order = cursor.fetchone()

        if not order:
            return jsonify({'error': 'ההזמנה לא קיימת או לא שייכת לספק'}), 403

        # ניצור מצב כך שאם ההזמנה לא במצב "ממתינה" אי אפשר לאשר אותה
        if order['status'] != 'ממתינה':
            return jsonify({
                'error': f'לא ניתן לעדכן סטטוס להזמנה בסטטוס "{order["status"]}"'
            }), 400

        # אם הכל תקין נעבור לסטטוס "בתהליך"
        cursor.execute("""
            UPDATE Orders 
            SET status = 'בתהליך' 
            WHERE order_id = %s
        """, (order_id,))
        conn.commit()

        return jsonify({'message': '✅ ההזמנה עודכנה לסטטוס "בתהליך"'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# צפייה בכל ההזמנות (בעל המכולת)
@app.route('/all_orders', methods=['GET'])
def all_orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # נקח את כל ההזמנות מהמערכת
        cursor.execute("SELECT * FROM Orders")
        orders = cursor.fetchall()

        return jsonify({'orders': orders}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# אישור קבלת הזמנה – משנה סטטוס ל"הושלמה" ומעדכן את המלאי בהתאם  (בעל המכולת)
@app.route('/complete_order', methods=['POST'])
def complete_order():
    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({'error': 'חסר מזהה הזמנה'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # נבדוק את הסטטוס הנוכחי של ההזמנה
        cursor.execute("SELECT status FROM Orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({'error': 'ההזמנה לא נמצאה'}), 404

        if order['status'] != 'בתהליך':
            return jsonify({'error': 'ניתן להשלים רק הזמנות בסטטוס "בתהליך"'}), 400

        # נעדכן את סטטוס ההזמנה ל"הושלמה"
        cursor.execute("UPDATE Orders SET status = 'הושלמה' WHERE order_id = %s", (order_id,))

        # נקח פריטי ההזמנה
        cursor.execute("""
            SELECT product_name, quantity
            FROM Order_Items
            WHERE order_id = %s
        """, (order_id,))
        items = cursor.fetchall()

        # נעדכן את המלאי על פי הפריטים שהוזמנו
        for item in items:
            name = item['product_name']
            qty = item['quantity']

            # נבדוק אם המוצר כבר קיים במלאי
            cursor.execute("SELECT * FROM Inventory WHERE product_name = %s", (name,))
            existing = cursor.fetchone()

            if existing:
                # אם קיים נעדכן את הכמות
                cursor.execute("""
                    UPDATE Inventory
                    SET current_quantity = current_quantity + %s
                    WHERE product_name = %s
                """, (qty, name))
            else:
                # אם לא – נכניס מוצר חדש עם הכמות שהוזמנה גם ככמות מינימלית
                cursor.execute("""
                    INSERT INTO Inventory (product_name, current_quantity, min_required)
                    VALUES (%s, %s, %s)
                """, (name, qty, qty))

        conn.commit()

        return jsonify({'message': 'ההזמנה הושלמה והמלאי עודכן ✅'}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# עדכון המלאי לאחר קנייה, וביצוע הזמנה אוטומטית למוצרים שחסרים (מקבל את הנתונים מהקופה)
@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    data = request.get_json()
    purchased_items = data.get("items", [])

    if not purchased_items:
        return jsonify({'error': 'לא נשלחו פריטים לעדכון.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    low_stock_items = []       # מוצרים שירדו מתחת לרף
    ignored_products = []      # מוצרים שאין להם ספק זמין
    supplier_orders = {}       # לכל ספק – רשימת מוצרים להזמנה

    try:
        # עדכון המלאי ובדיקה מה ירד מתחת למינימום
        for item in purchased_items:
            name = item.get("product_name")
            quantity = item.get("quantity")

            if name is None or quantity is None:
                continue

            # עדכון הכמות הנוכחית
            cursor.execute("""
                UPDATE Inventory
                SET current_quantity = current_quantity - %s
                WHERE product_name = %s
            """, (quantity, name))

            # בדיקה אם ירד מתחת לכמות המינימום
            cursor.execute("""
                SELECT current_quantity, min_required
                FROM Inventory
                WHERE product_name = %s
            """, (name,))
            result = cursor.fetchone()

            if result and result['current_quantity'] < result['min_required']:
                needed_quantity = result['min_required'] - result['current_quantity']

                #מציאת ספק הזול ביותר
                cursor.execute("""
                    SELECT supplier_name, price, min_quantity 
                    FROM Products
                    WHERE product_name = %s
                    ORDER BY price ASC
                    LIMIT 1
                """, (name,))
                supplier = cursor.fetchone()

                if not supplier:
                    ignored_products.append(f"{name} - אין ספק זמין למוצר זה")
                    continue

                supplier_name = supplier['supplier_name']
                min_quantity = supplier['min_quantity']
                order_quantity = max(min_quantity, needed_quantity)

                # ריכוז פריטים לפי ספק
                if supplier_name not in supplier_orders:
                    supplier_orders[supplier_name] = []
                supplier_orders[supplier_name].append({
                    'product_name': name,
                    'quantity': order_quantity
                })

                low_stock_items.append(name)

        #יצירת הזמנות לפי ספק
        created_orders = []
        for supplier_name, items in supplier_orders.items():
            response, code = create_order_for_supplier(supplier_name, items, conn)
            if code == 201:
                created_orders.append(response['order_id'])

        # רק אחרי הכול נבצע שמירה של השינויים
        conn.commit()

        return jsonify({
            'message': ' המלאי עודכן בהצלחה.',
            'products_below_min': low_stock_items,
            'orders_created': created_orders,
            'ignored_products': ignored_products
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({
            'error': 'אירעה שגיאה בעת עדכון המלאי.',
            'details': str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()

# עדכון הספק על ההזמנות שהושלמו ועוד לא עודכן על כך (עבור צד הספק) 
@app.route("/newly_completed_orders", methods=["GET"])
def newly_completed_orders():
    company_name = request.args.get("company_name")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # שליפת הזמנות שהושלמו וטרם נצפו
    cursor.execute("""
        SELECT order_id, status
        FROM orders
        WHERE supplier_name = %s AND status = 'הושלמה' AND seen_by_supplier = FALSE
    """, (company_name,))
    orders = cursor.fetchall()

    # אם אין הזמנות חדשות, מחזירים הודעה מתאימה
    if not orders:
        return jsonify({"message": " אין הזמנות חדשות שהושלמו", "orders": []})

    # עדכון כל ההזמנות ל-seen
    cursor.execute("""
        UPDATE orders
        SET seen_by_supplier = TRUE
        WHERE supplier_name = %s AND status = 'הושלמה' AND seen_by_supplier = FALSE
    """, (company_name,))
    conn.commit()

    return jsonify({"orders": orders})

# להריץ את השרת
if __name__ == "__main__":
    app.run(debug=True)