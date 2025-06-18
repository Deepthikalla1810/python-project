import datetime
import sqlite3
import pandas as pd
from tkcalendar import DateEntry
from tkinter import *
import tkinter.messagebox as mb
import tkinter.ttk as ttk
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import calendar  # For getting month names

# Connecting to the Database
connector = sqlite3.connect("Expense Tracker.db")
cursor = connector.cursor()

cursor.execute(
    'CREATE TABLE IF NOT EXISTS ExpenseTracker (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, Date DATETIME, Payee TEXT, Description TEXT, Amount FLOAT, ModeOfPayment TEXT, Category TEXT)'
)
connector.commit()

# Functions
def list_all_expenses():
    global connector, table
    table.delete(*table.get_children())
    all_data = connector.execute('SELECT * FROM ExpenseTracker')
    data = all_data.fetchall()

    for values in data:
        table.insert('', END, values=values)

def view_expense_details():
    global table, date, payee, desc, amnt, MoP, category
    if not table.selection():
        mb.showerror('No expense selected', 'Please select an expense from the table to view its details')
        return

    current_selected_expense = table.item(table.focus())
    values = current_selected_expense['values']

    expenditure_date = datetime.date(int(values[1][:4]), int(values[1][5:7]), int(values[1][8:]))
    date.set_date(expenditure_date)
    payee.set(values[2])
    desc.set(values[3])
    amnt.set(values[4])
    MoP.set(values[5])
    category.set(values[6])

def clear_fields():
    global desc, payee, amnt, MoP, date, category, table
    today_date = datetime.datetime.now().date()
    desc.set('')
    payee.set('')
    amnt.set(0.0)
    MoP.set('Cash')
    category.set('Food')
    date.set_date(today_date)
    table.selection_remove(*table.selection())

def remove_expense():
    if not table.selection():
        mb.showerror('No record selected!', 'Please select a record to delete!')
        return

    current_selected_expense = table.item(table.focus())
    values_selected = current_selected_expense['values']

    surety = mb.askyesno('Are you sure?', f'Are you sure that you want to delete the record of {values_selected[2]}?')
    if surety:
        connector.execute('DELETE FROM ExpenseTracker WHERE ID=?', (values_selected[0],))
        connector.commit()
        list_all_expenses()
        mb.showinfo('Record deleted successfully!', 'The record you wanted to delete has been deleted successfully.')

def remove_all_expenses():
    surety = mb.askyesno('Are you sure?', 'Are you sure that you want to delete all the expense items from the database?', icon='warning')
    if surety:
        connector.execute('DELETE FROM ExpenseTracker')
        connector.commit()
        clear_fields()
        list_all_expenses()
        mb.showinfo('All Expenses deleted', 'All the expenses were successfully deleted.')
    else:
        mb.showinfo('Ok then', 'The task was aborted and no expense was deleted!')

def add_another_expense():
    global date, payee, desc, amnt, MoP, category, connector

    if not date.get() or not payee.get() or not desc.get() or not amnt.get() or not MoP.get() or not category.get():
        mb.showerror('Fields empty!', "Please fill all the missing fields before pressing the add button!")
    else:
        connector.execute(
            'INSERT INTO ExpenseTracker (Date, Payee, Description, Amount, ModeOfPayment, Category) VALUES (?, ?, ?, ?, ?, ?)',
            (date.get_date(), payee.get(), desc.get(), amnt.get(), MoP.get(), category.get())
        )
        connector.commit()
        clear_fields()
        list_all_expenses()
        mb.showinfo('Expense added', 'The expense whose details you just entered has been added to the database.')

def edit_expense():
    global table

    def edit_existing_expense():
        global date, amnt, desc, payee, MoP, category, connector
        current_selected_expense = table.item(table.focus())
        contents = current_selected_expense['values']

        connector.execute(
            'UPDATE ExpenseTracker SET Date=?, Payee=?, Description=?, Amount=?, ModeOfPayment=?, Category=? WHERE ID=?',
            (date.get_date(), payee.get(), desc.get(), amnt.get(), MoP.get(), category.get(), contents[0])
        )
        connector.commit()

        clear_fields()
        list_all_expenses()
        mb.showinfo('Data edited', 'We have updated the data and stored it in the database as you wanted.')
        edit_btn.destroy()

    if not table.selection():
        mb.showerror('No expense selected!', 'You have not selected any expense in the table for us to edit; please do that!')
        return

    view_expense_details()

    edit_btn = Button(data_entry_frame, text='Edit expense', font=btn_font, width=30, bg=hlb_btn_bg, command=edit_existing_expense)
    edit_btn.place(x=10, y=400)

def summarize_expenses():
    summary_window = Toplevel(root)
    summary_window.title("Expense Summary")
    summary_window.geometry("600x600")
    summary_window.configure(bg='#E9ECEF')  # Light grey background

    Label(summary_window, text="Monthly Expense Summary", font=("Helvetica", 20, 'bold'), bg='#E9ECEF', fg='#343A40').pack(pady=20)

    monthly_summary = {}
    yearly_total = 0

    for row in connector.execute('SELECT strftime("%Y-%m", Date) as month, Category, SUM(Amount) FROM ExpenseTracker GROUP BY month, Category'):
        month, category, total = row
        yearly_total += total

        if month not in monthly_summary:
            monthly_summary[month] = {}
        monthly_summary[month][category] = total

    monthly_frame = Frame(summary_window, bg='#FFFFFF', bd=2, relief='flat')
    monthly_frame.pack(pady=20, padx=10, fill='both', expand=True)

    for month in sorted(monthly_summary.keys()):
        month_year = month.split('-')
        month_name = calendar.month_name[int(month_year[1])]
        year = month_year[0]

        month_header = Frame(monthly_frame, bg='#007BFF')
        month_header.pack(fill='x', padx=10, pady=(10, 0))

        Label(month_header, text=f"{month_name} {year}", font=("Helvetica", 16, 'bold'), bg='#007BFF', fg='white').pack(pady=10)

        total_month = 0
        for category, amount in monthly_summary[month].items():
            Label(monthly_frame, text=f"{category}: ₹{amount:.2f}", anchor='w', bg='#FFFFFF', fg='#333').pack(anchor='w', padx=20, pady=5)
            total_month += amount

        Label(monthly_frame, text=f"Total for {month_name} {year}: ₹{total_month:.2f}", font=("Helvetica", 14, 'italic'), bg='#F8F9FA', fg='#007BFF').pack(anchor='w', padx=20, pady=(5, 10))

    yearly_frame = Frame(summary_window, bg='#F1F1F1', bd=2, relief='flat')
    yearly_frame.pack(pady=20, padx=10, fill='both', expand=True)

    Label(yearly_frame, text="--- Total Yearly Expenses ---", font=("Helvetica", 18, 'bold'), bg='#F1F1F1', fg='#343A40').pack(pady=10)
    Label(yearly_frame, text=f"Total Yearly Expense: ₹{yearly_total:.2f}", font=("Helvetica", 16), bg='#F1F1F1', fg='#343A40').pack(pady=10)

    close_btn = Button(summary_window, text="Close", command=summary_window.destroy, font=("Helvetica", 12), bg='#007BFF', fg='white', bd=0, padx=10, pady=5)
    close_btn.pack(pady=20)

    close_btn.bind("<Enter>", lambda e: close_btn.configure(bg='#0056b3'))
    close_btn.bind("<Leave>", lambda e: close_btn.configure(bg='#007BFF'))

def visualize_expenses():
    data = connector.execute('SELECT strftime("%Y-%m", Date) as month, Category, SUM(Amount) FROM ExpenseTracker GROUP BY month, Category').fetchall()

    categories = ['Food', 'Fun', 'Work', 'Misc', 'Home']
    month_expenses = {}
    
    for row in data:
        month, category, total = row
        if month not in month_expenses:
            month_expenses[month] = {cat: 0 for cat in categories}
        month_expenses[month][category] += total

    months = list(month_expenses.keys())
    x = np.arange(len(months))
    width = 0.15

    for i, category in enumerate(categories):
        heights = [month_expenses[month][category] for month in months]
        plt.bar(x + i * width, heights, width, label=category)

    plt.xlabel('Months')
    plt.ylabel('Amount')
    plt.title('Monthly Expenses by Category')
    plt.xticks(x + width, months)
    plt.legend(title='Categories')
    plt.tight_layout()
    plt.show()

# AI Suggestion Function
def ai_spending_suggestions():
    data = connector.execute('SELECT Date, Category, Amount FROM ExpenseTracker').fetchall()
    
    if len(data) < 10:  # Ensure sufficient data for AI-based suggestions
        mb.showinfo('Insufficient Data', 'Add more expense data to get AI-based suggestions.')
        return

    df = pd.DataFrame(data, columns=['Date', 'Category', 'Amount'])
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')

    monthly_expenses = df.groupby('Month')['Amount'].sum().reset_index()

    monthly_expenses['MonthIndex'] = range(len(monthly_expenses))
    X = monthly_expenses[['MonthIndex']]
    y = monthly_expenses['Amount']

    model = LinearRegression()
    model.fit(X, y)
    predicted_expense = model.predict([[len(monthly_expenses)]])

    category_spending = df.groupby('Category')['Amount'].sum().reset_index()
    top_category = category_spending.loc[category_spending['Amount'].idxmax()]

    suggestion_message = (
        f"🔮 *AI Spending Suggestions*:\n\n"
        f"- Based on your data, next month's predicted total expense is: ₹{predicted_expense[0]:.2f}.\n"
        f"- Your highest spending category so far is '{top_category['Category']}' with a total of ₹{top_category['Amount']:.2f}.\n"
        f"- Try limiting your expenses in the '{top_category['Category']}' category if needed.\n"
        f"- You might want to set a spending limit for the next month to ₹{(predicted_expense[0] * 0.9):.2f}."
    )

    mb.showinfo("AI Expense Suggestions", suggestion_message)

# Backgrounds and Fonts
data_entry_frame_bg = 'Red'
buttons_frame_bg = 'Tomato'
hlb_btn_bg = 'IndianRed'

lbl_font = ('Georgia', 13)
entry_font = 'Times 13 bold'
btn_font = ('Gill Sans MT', 13)

# Initializing the GUI window
root = Tk()
root.title('Personal Expense Tracker')
root.geometry('1000x700')  # Adjusted size for better layout
root.resizable(0, 0)

Label(root, text='EXPENSE TRACKER', font=('Noto Sans CJK TC', 20, 'bold'), bg=hlb_btn_bg).pack(side=TOP, fill=X)

# StringVar and DoubleVar variables
desc = StringVar()
amnt = DoubleVar()
payee = StringVar()
MoP = StringVar(value='Cash')
category = StringVar(value='Food')

# Frames
data_entry_frame = Frame(root, bg='white')
data_entry_frame.place(x=10, y=50, relheight=0.65, relwidth=0.30)

buttons_frame = Frame(root, bg='pink')
buttons_frame.place(relx=0.30, rely=0.05, relwidth=0.70, relheight=0.25)

tree_frame = Frame(root)
tree_frame.place(relx=0.30, rely=0.30, relwidth=0.70, relheight=0.65)

# Data Entry Frame
Label(data_entry_frame, text='Date (YYYY-MM-DD):', font=lbl_font, bg='white').place(x=10, y=20)
date = DateEntry(data_entry_frame, date=datetime.datetime.now().date(), font=entry_font)
date.place(x=10, y=60, width=150)

Label(data_entry_frame, text='Payee:', font=lbl_font, bg='white').place(x=10, y=100)
Entry(data_entry_frame, textvariable=payee, font=entry_font).place(x=10, y=130, width=150)

Label(data_entry_frame, text='Description:', font=lbl_font, bg='white').place(x=10, y=170)
Entry(data_entry_frame, textvariable=desc, font=entry_font).place(x=10, y=200, width=150)

Label(data_entry_frame, text='Amount:', font=lbl_font, bg='white').place(x=10, y=240)
Entry(data_entry_frame, textvariable=amnt, font=entry_font).place(x=10, y=270, width=150)

Label(data_entry_frame, text='Mode of Payment:', font=lbl_font, bg='white').place(x=10, y=310)
OptionMenu(data_entry_frame, MoP, 'Cash', 'Card', 'Online').place(x=10, y=340)

Label(data_entry_frame, text='Category:', font=lbl_font, bg='white').place(x=10, y=380)
OptionMenu(data_entry_frame, category, 'Food', 'Fun', 'Work', 'Misc', 'Home').place(x=10, y=410)

# Buttons

Button(buttons_frame, text='Add Expense', font=btn_font, bg=hlb_btn_bg, command=add_another_expense).grid(row=0, column=0, padx=10, pady=5, sticky='ew')
Button(buttons_frame, text='View Selected Expense', font=btn_font, bg=hlb_btn_bg, command=view_expense_details).grid(row=0, column=1, padx=10, pady=5, sticky='ew')
Button(buttons_frame, text='Edit Expense', font=btn_font, bg=hlb_btn_bg, command=edit_expense).grid(row=0, column=2, padx=10, pady=5, sticky='ew')
Button(buttons_frame, text='Remove Expense', font=btn_font, bg=hlb_btn_bg, command=remove_expense).grid(row=0, column=3, padx=10, pady=5, sticky='ew')

Button(buttons_frame, text='Remove All Expenses', font=btn_font, bg=hlb_btn_bg, command=remove_all_expenses).grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='ew')
Button(buttons_frame, text='Summarize Expenses', font=btn_font, bg=hlb_btn_bg, command=summarize_expenses).grid(row=1, column=2, padx=10, pady=5, sticky='ew')
Button(buttons_frame, text='Visualize Expenses', font=btn_font, bg=hlb_btn_bg, command=visualize_expenses).grid(row=1, column=3, padx=10, pady=5, sticky='ew')

Button(buttons_frame, text='AI Suggestions', font=btn_font, bg=hlb_btn_bg, command=ai_spending_suggestions).grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky='ew')

# Treeview for displaying expenses
columns = ('ID', 'Date', 'Payee', 'Description', 'Amount', 'ModeOfPayment', 'Category')
table = ttk.Treeview(tree_frame, columns=columns, show='headings')
table.heading('ID', text='ID')
table.heading('Date', text='Date')
table.heading('Payee', text='Payee')
table.heading('Description', text='Description')
table.heading('Amount', text='Amount')
table.heading('ModeOfPayment', text='Mode of Payment')
table.heading('Category', text='Category')
table.column('ID', width=50)
table.column('Date', width=100)
table.column('Payee', width=100)
table.column('Description', width=150)
table.column('Amount', width=100)
table.column('ModeOfPayment', width=100)
table.column('Category', width=100)
table.pack(fill=BOTH, expand=True)

# Initialize and populate the table
list_all_expenses()

# Run the application
root.mainloop()

# Close the database connection
connector.close()