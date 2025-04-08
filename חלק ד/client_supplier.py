# client_supplier.py
# לקוח צד ספק - התחברות או רישום מערכת

import requests

# כתובת השרת המקומית
BASE_URL = "http://127.0.0.1:5000"

# נשמור את שם החברה לאחר התחברות/רישום כדי להיות מחוברים
company_name = None

# פונקציה להתחברות או רישום של ספק
def login_or_register():
    global company_name

    # בקשת שם החברה מהמשתמש
    company_name = input("הזן את שם החברה שלך: ")

    # ניסיון התחברות לספק קיים
    response = requests.post(f"{BASE_URL}/login_or_register_supplier", json={
        "company_name": company_name
    })

    # במידה והספק קיים
    if response.status_code == 200:
        print(" התחברת בהצלחה!")
        return True

    # אם הספק לא קיים נעבור לרישום
    elif response.status_code == 400:
        print(" הספק לא קיים. נבצע רישום.")

        phone_number = input("הזן את מספר הטלפון של החברה: ")
        representative_name = input("הזן את שם הנציג/ה: ")

        # קבלת מספר המוצרים בסחורה של הספק
        try:
            num_products = int(input("כמה מוצרים ברצונך לרשום? "))
        except ValueError:
            print(" שגיאה: נא להזין מספר תקין.")
            return False

        # בניית רשימת מוצרים עם נתונים
        products = []
        for i in range(num_products):
            print(f"\n--- מוצר מספר {i + 1} ---")
            product_name = input("שם המוצר: ")
            try:
                price = float(input("מחיר ליחידה: "))
                min_quantity = int(input("כמות מינימלית להזמנה: "))
            except ValueError:
                print("נא להזין ערכים מספריים תקינים.")
                return False

            products.append({
                "product_name": product_name,
                "price": price,
                "min_quantity": min_quantity
            })

        # שליחת נתוני הספק + מוצרים לרישום
        response = requests.post(f"{BASE_URL}/login_or_register_supplier", json={
            "company_name": company_name,
            "phone_number": phone_number,
            "representative_name": representative_name,
            "products": products
        })

        if response.status_code == 201:
            print("ההרשמה הושלמה והתחברת בהצלחה!")
            return True
        else:
            print("שגיאה בהרשמה:", response.json().get("error", "שגיאה לא ידועה"))
            company_name = None
            return False

    # שגיאה כללית (לא 200 ולא 400)
    else:
        print("שגיאה בהתחברות:", response.json().get("error", "שגיאה לא ידועה"))
        company_name = None
        return False

# צפייה בהזמנות של הספק הנוכחי
def view_orders():
    # שליחת בקשה לשרת לקבלת ההזמנות של הספק לפי שם החברה
    response = requests.get(f"{BASE_URL}/supplier_orders", params={"company_name": company_name})

    if response.status_code == 200:
        # חילוץ רשימת ההזמנות מתוך תגובת השרת
        orders = response.json().get("orders", [])

        # בדיקה אם קיימות הזמנות
        if not orders:
            print("אין הזמנות להצגה כרגע.")
            return

        # הדפסת ההזמנות הקיימות
        print("\n--- ההזמנות שהתקבלו ---")
        for order in orders:
            print(f"מזהה הזמנה: {order['order_id']} | סטטוס נוכחי: {order['status']}")
    else:
        # במקרה של שגיאה מהשרת
        print(" שגיאה בעת קבלת ההזמנות:", response.json().get("error", "שגיאה לא ידועה"))

#  פונקציה להצגת הפריטים בהזמנה מסוימת של הספק (נוסיף גם הצגה של סטטוס ההזמנה)
def view_order_items():
    # בקשת מזהה הזמנה מהמשתמש
    order_id = input(" הזן מזהה הזמנה שברצונך לצפות בפריטיה: ")

    # שליחת בקשה לשרת עם מזהה ההזמנה ושם החברה
    response = requests.get(f"{BASE_URL}/order_items", params={
        "order_id": order_id,
        "company_name": company_name
    })

    if response.status_code == 200:
        # קבלת הנתונים מתוך תגובת השרת
        data = response.json()
        items = data.get("items", [])
        status = data.get("status", "לא ידוע")

        # הצגת סטטוס ההזמנה ופריטיה
        print(f"\n --- פרטי ההזמנה --- (סטטוס נוכחי: {status})")
        if not items:
            print("ההזמנה לא כוללת פריטים.")
            return

        for item in items:
            print(f" מוצר: {item['product_name']} | כמות: {item['quantity']}")

    else:
        # טיפול בשגיאות
        error_message = response.json().get("error", response.json().get("message", "שגיאה לא ידועה"))
        print(" שגיאה בקבלת פרטי ההזמנה:", error_message)

# פונקציה לעדכון סטטוס הזמנה ל"בתהליך" ע"י הספק
def update_order_status():
    # בקשת מזהה הזמנה מהמשתמש
    order_id = input("הזן את מזהה הזמנה שברצונך לעדכן ל'בתהליך': ")

    # שליחת בקשה לשרת עם פרטי ההזמנה והספק
    response = requests.post(f"{BASE_URL}/update_order_status", json={
        "order_id": order_id,
        "company_name": company_name
    })

    # בדיקה האם העדכון הצליח
    if response.status_code == 200:
        print("ההזמנה עודכנה בהצלחה לסטטוס 'בתהליך'.")
    else:
        # טיפול בשגיאות: אם קיימת הודעת שגיאה ברורה מהשרת – נציג אותה
        error_message = response.json().get("error", "שגיאה לא ידועה התרחשה.")
        print(f"לא ניתן לעדכן את ההזמנה: {error_message}")

#פונקציה לצפיה בהזמנות מאותו הלקוח שבינתיים בעל המכולת קיבל וסימן כהושלמה
def view_newly_completed_orders():
    response = requests.get(f"{BASE_URL}/newly_completed_orders", params={
        "company_name": company_name
    })

    if response.status_code == 200:
        orders = response.json().get("orders", [])
        if orders:
            print("\n--- הזמנות שהושלמו לאחרונה ---")
            for order in orders:
                print(f"מזהה: {order['order_id']} | סטטוס: {order['status']}")
        else:
            print("\nאין הזמנות חדשות שהושלמו מאז החיבור האחרון.")
    else:
        print("שגיאה בשליפת הזמנות חדשות שהושלמו.")

def main():
    # ניסיון התחברות או הרשמה – אם לא הצליח נסיים את התהליך
    if not login_or_register():
        print("לא ניתן להתחבר או להירשם.")
        return

    # לולאה אינסופית לממשק הפעולות של הספק
    while True:
        print("\n --- ממשק ניהול לספק ---")
        print("1. צפייה בכל ההזמנות שקיבלת")
        print("2. צפייה בפרטים של הזמנה מסוימת")
        print("3. אישור הזמנה (עדכון ל'בתהליך')")
        print("4. צפייה בהזמנות חדשות שההתקבלו והושלמו על ידי בעל המכולת)")
        print("5. יציאה מהמערכת")

        # קבלת בחירה מהמשתמש
        choice = input("בחר פעולה (1 / 2 / 3 / 4 / 5): ")

        # ביצוע הפעולה בהתאם לבחירת המשתמש
        if choice == "1":
            view_orders()
        elif choice == "2":
            view_order_items()
        elif choice == "3":
            update_order_status()
        elif choice == "4":
            view_newly_completed_orders()  # כאן נשתמש בפונקציה שתכף אשלח
        elif choice == "5":
            print("להתראות! תודה שהשתמשת במערכת.")
            break
        else:
            print("בחירה לא תקינה. נסה שוב על ידי הקשת 1 עד 5.")

if __name__ == "__main__":
    main()
