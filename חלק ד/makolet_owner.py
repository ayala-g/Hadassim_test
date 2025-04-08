# makolet_owner.py
# לקוח צד בעל המכולת - יצירת הזמנות

import requests

# כתובת השרת המקומי של ה-API
BASE_URL = "http://127.0.0.1:5000"

#פונקציה ליצירת הזמנה חדשה על ידי בעל המכולת
def create_order():
    # בקשת שם הספק ממנו תתבצע ההזמנה
    supplier_name = input("הזן את שם הספק להזמנה: ")

    # קבלת מספר המוצרים בהזמנה
    try:
        num_products = int(input("הזן את כמות המוצרים בהזמנה: "))
    except ValueError:
        print(" נא להזין מספר תקין.")
        return

    # איסוף פרטי כל מוצר להזמנה
    products = []
    for i in range(num_products):
        product_name = input(f"הזן שם מוצר מספר {i+1}: ")
        try:
            quantity = int(input("הזן כמות: "))
        except ValueError:
            print("נא להזין כמות מספרית בלבד.")
            return

        products.append({
            'product_name': product_name,
            'quantity': quantity
        })

    # שליחת ההזמנה לשרת
    response = requests.post(f"{BASE_URL}/create_order", json={
        'company_name': supplier_name,
        'items': products
    })

    # טיפול בתגובה המתקבלת מהשרת
    if response.status_code == 201:
        data = response.json()
        print(" ההזמנה נוצרה בהצלחה.")
        print("מזהה ההזמנה שלך:", data.get("order_id"))

        # בדיקת מוצרים שנפסלו ולא נוספו להזמנה
        ignored_items = data.get("ignored_items", [])
        if ignored_items:
            print("שים לב: חלק מהמוצרים לא נוספו להזמנה:")
            for error in ignored_items:
                print(" -", error)

    else:
        print("שגיאה ביצירת ההזמנה:")
        try:
            error = response.json().get('error', 'שגיאה לא ידועה')
            print(" -", error)

            details = response.json().get("details")
            if details:
                print("פריטים שלא עברו אימות:")
                for err in details:
                    print(" -", err)
        except:
            print("לא ניתן לקרוא את פרטי השגיאה מהשרת.")

#הצגת כל ההזמנות לבעל המכולת
def view_all_orders():
    # שליחת בקשה לשרת לקבל את כל ההזמנות
    response = requests.get(f"{BASE_URL}/all_orders")

    if response.status_code == 200:
        # חילוץ רשימת ההזמנות מהתגובה
        orders = response.json().get('orders', [])

        if not orders:
            print(" אין הזמנות להצגה כרגע.")
            return

        print("\n --- כל ההזמנות במערכת ---")
        for order in orders:
            print(f" מזהה הזמנה: {order['order_id']}")
            print(f" ספק: {order['supplier_name']}")
            print(f" סטטוס: {order['status']}")
            print("-" * 30)

    else:
        print(" שגיאה בעת ניסיון לקבל את רשימת ההזמנות מהשרת.")

#פונקציה להשלמת הזמנה ע"י בעל המכולת-שינוי סטטוס ההזמנה ל"הושלמה" ועדכות כמות המוצרים בחנות
def complete_order():
    # קליטת מזהה הזמנה מהמשתמש
    order_id = input(" הזן מזהה הזמנה שתרצה לסמן כהושלמה: ")

    try:
        # שליחת בקשת לשרת לעדכון סטטוס ההזמנה
        response = requests.post(f"{BASE_URL}/complete_order", json={'order_id': order_id})
        
        if response.status_code == 200:
            print("סטטוס ההזמנה עודכן בהצלחה כ'הושלמה'.")
        elif response.status_code == 400:
            # שגיאה אם ההזמנה כבר הושלמה או בסטטוס לא תקין
            error_message = response.json().get('error', 'ההזמנה לא בתהליך')
            print(" שגיאה לוגית:", error_message)
        elif response.status_code == 404:
            # אם אין מזהה כזה בשרת
            print(" לא נמצאה הזמנה עם מזהה זה.")
        else:
            # שגיאה אחרת
            error_message = response.json().get('error', 'שגיאה לא ידועה.')
            print(" שגיאה בעדכון ההזמנה:", error_message)

    except Exception as e:
        # טיפול בשגיאות כלליות
        print("שגיאה  בביצוע הבקשה:", str(e))

def main():
    while True:
        # תפריט ראשי למערכת ניהול המכולת
        print("\n מערכת לניהול מכולת - תפריט ראשי ")
        print("1  יצירת הזמנה חדשה")
        print("2 צפייה בכל ההזמנות")
        print("3  אישור קבלת הזמנה (סימון כהושלמה)")
        print("4  יציאה מהמערכת")

        choice = input(" בחר פעולה (1/2/3/4): ")

        # טיפול בבחירת המשתמש
        if choice == "1":
            create_order()
        elif choice == "2":
            view_all_orders()
        elif choice == "3":
            complete_order()
        elif choice == "4":
            print(" להתראות! תודה שהשתמשת במערכת.")
            break
        else:
            print(" בחירה לא תקינה, נסה שוב.")

if __name__ == "__main__":
    main()
