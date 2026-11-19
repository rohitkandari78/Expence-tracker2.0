/**
 * ==========================================================================
 * DATA CLASSES & PERSISTENCE ENGINE (SPATIAL & SALARY TRACKING)
 * ==========================================================================
 */

/**
 * User Class
 * Represents a user with budgets, expenses, and salary/income tracking
 */
class User {
    constructor(uid, email, displayName, photoURL, isGuest = false) {
        this.uid = uid;
        this.email = email;
        this.displayName = displayName;
        this.photoURL = photoURL;
        this.budgets = {}; // Stored by "YYYY-M" key e.g. "2026-9": 45000
        this.salaries = {}; // Stored by "YYYY-M" key e.g. "2026-9": { amount: 75000, employer: "Google", payDay: 1 }
        this.employer = '';
        this.expenses = [];
        this.isGuest = isGuest;
    }

    /**
     * Set the user's budget for a specific month
     */
    setBudget(amount, month = null, year = null) {
        const now = new Date();
        const budgetMonth = month !== null ? month : now.getMonth();
        const budgetYear = year !== null ? year : now.getFullYear();
        const monthKey = `${budgetYear}-${budgetMonth}`;
        this.budgets[monthKey] = parseFloat(amount) || 0;
    }

    /**
     * Get budget for a specific month
     */
    getBudget(month = null, year = null) {
        const now = new Date();
        const budgetMonth = month !== null ? month : now.getMonth();
        const budgetYear = year !== null ? year : now.getFullYear();
        const monthKey = `${budgetYear}-${budgetMonth}`;
        return this.budgets[monthKey] || 0;
    }

    /**
     * Set the user's salary / employment details for a specific month
     */
    setSalary(amount, month = null, year = null, employer = '', payDay = 1) {
        const now = new Date();
        const salaryMonth = month !== null ? month : now.getMonth();
        const salaryYear = year !== null ? year : now.getFullYear();
        const monthKey = `${salaryYear}-${salaryMonth}`;
        
        if (employer) this.employer = employer;
        this.salaries[monthKey] = {
            amount: parseFloat(amount) || 0,
            employer: employer || this.employer,
            payDay: parseInt(payDay) || 1
        };
    }

    /**
     * Get salary details for a specific month
     */
    getSalary(month = null, year = null) {
        const now = new Date();
        const salaryMonth = month !== null ? month : now.getMonth();
        const salaryYear = year !== null ? year : now.getFullYear();
        const monthKey = `${salaryYear}-${salaryMonth}`;
        
        if (this.salaries[monthKey]) {
            return this.salaries[monthKey].amount;
        }

        // Fallback: check if any recent salary was set
        const keys = Object.keys(this.salaries);
        if (keys.length > 0) {
            return this.salaries[keys[keys.length - 1]].amount || 0;
        }
        return 0;
    }

    /**
     * Get employer name
     */
    getEmployer(month = null, year = null) {
        const now = new Date();
        const salaryMonth = month !== null ? month : now.getMonth();
        const salaryYear = year !== null ? year : now.getFullYear();
        const monthKey = `${salaryYear}-${salaryMonth}`;
        
        if (this.salaries[monthKey] && this.salaries[monthKey].employer) {
            return this.salaries[monthKey].employer;
        }
        return this.employer || '';
    }

    /**
     * Add an expense/income transaction
     */
    addExpense(expense) {
        this.expenses.push(expense);
    }

    /**
     * Remove an expense by ID
     */
    removeExpense(expenseId) {
        this.expenses = this.expenses.filter(e => e.id !== expenseId);
    }

    /**
     * Get total amount spent (only expense transactions, excluding income)
     */
    getTotalSpent(month = null, year = null) {
        const items = this.getExpensesForMonth(month, year);
        return items
            .filter(e => e.type !== 'income')
            .reduce((total, expense) => total + expense.amount, 0);
    }

    /**
     * Get total income received (Base Monthly Salary + any income credits like Bonus/Freelance)
     */
    getTotalIncome(month = null, year = null) {
        const baseSalary = this.getSalary(month, year);
        const items = this.getExpensesForMonth(month, year);
        
        // Sum additional income credits (excluding Base Salary if logged separately)
        const incomeCredits = items
            .filter(e => e.type === 'income')
            .reduce((total, item) => total + item.amount, 0);

        // If salary is logged as a transaction or as base salary, avoid double count
        const hasSalaryTransaction = items.some(e => e.type === 'income' && (e.category === 'Salary' || e.category === 'Monthly Salary'));
        
        if (hasSalaryTransaction) {
            return incomeCredits;
        }
        return baseSalary + incomeCredits;
    }

    /**
     * Get net in-pocket savings for the month: Total Income - Total Spent
     */
    getNetSavings(month = null, year = null) {
        return this.getTotalIncome(month, year) - this.getTotalSpent(month, year);
    }

    /**
     * Get savings rate percentage: (Net Savings / Total Income) * 100
     */
    getSavingsPercentage(month = null, year = null) {
        const income = this.getTotalIncome(month, year);
        if (income <= 0) return 0;
        const savings = this.getNetSavings(month, year);
        return Math.max(0, (savings / income) * 100);
    }

    /**
     * Get remaining budget balance
     */
    getRemainingBalance(month = null, year = null) {
        const budget = this.getBudget(month, year);
        return budget - this.getTotalSpent(month, year);
    }

    /**
     * Get spending percentage against budget
     */
    getSpendingPercentage(month = null, year = null) {
        const budget = this.getBudget(month, year);
        if (budget === 0) return 0;
        return (this.getTotalSpent(month, year) / budget) * 100;
    }

    /**
     * Check if over budget
     */
    isOverBudget(month = null, year = null) {
        const budget = this.getBudget(month, year);
        return budget > 0 && this.getTotalSpent(month, year) > budget;
    }

    /**
     * Get expenses for a specific month
     */
    getExpensesForMonth(month = null, year = null) {
        const now = new Date();
        const m = month !== null ? month : now.getMonth();
        const y = year !== null ? year : now.getFullYear();
        
        return this.expenses.filter(expense => {
            const expenseDate = new Date(expense.date);
            return expenseDate.getMonth() === m && expenseDate.getFullYear() === y;
        });
    }

    /**
     * Convert to Firebase document format
     */
    toFirestore() {
        return {
            uid: this.uid,
            email: this.email,
            displayName: this.displayName,
            photoURL: this.photoURL,
            budgets: this.budgets,
            salaries: this.salaries,
            employer: this.employer || '',
            createdAt: firebase.firestore.FieldValue.serverTimestamp()
        };
    }

    /**
     * Create User from Firebase document
     */
    static fromFirestore(doc) {
        const data = doc.data();
        const user = new User(
            doc.id,
            data.email,
            data.displayName,
            data.photoURL
        );
        if (data.budgets) user.budgets = data.budgets;
        if (data.salaries) user.salaries = data.salaries;
        if (data.employer) user.employer = data.employer;

        // Handle legacy single budget
        if (data.budget && !data.budgets) {
            const now = new Date();
            user.setBudget(data.budget, now.getMonth(), now.getFullYear());
        }
        return user;
    }
}

/**
 * Budget Class
 * Represents a monthly budget
 */
class Budget {
    constructor(amount, month = null, year = null) {
        this.amount = parseFloat(amount) || 0;
        const now = new Date();
        this.month = month !== null ? month : now.getMonth();
        this.year = year !== null ? year : now.getFullYear();
    }

    isExceeded(totalExpenses) {
        return totalExpenses > this.amount;
    }

    getPercentageUsed(totalExpenses) {
        if (this.amount === 0) return 0;
        return (totalExpenses / this.amount) * 100;
    }

    getRemaining(totalExpenses) {
        return this.amount - totalExpenses;
    }
}

/**
 * Expense / Transaction Class
 * Represents a transaction (either Expense 🔴 or Income/Salary 🟢)
 */
class Expense {
    constructor(amount, category, description, date, type = 'expense') {
        this.id = this.generateId();
        this.amount = parseFloat(amount) || 0;
        this.category = category;
        this.description = description;
        this.date = date;
        this.type = type; // 'expense' or 'income'
        this.splitWith = [];
        this.createdAt = new Date();
    }

    generateId() {
        return `tx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    splitBetween(people) {
        this.splitWith = people;
        return this.getAmountPerPerson();
    }

    getAmountPerPerson() {
        if (this.splitWith.length === 0) return this.amount;
        return this.amount / (this.splitWith.length + 1);
    }

    isSplit() {
        return this.splitWith.length > 0;
    }

    isIncome() {
        return this.type === 'income';
    }

    getFormattedDate() {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(this.date).toLocaleDateString('en-IN', options);
    }

    getCategoryEmoji() {
        const emojiMap = {
            // Expenses
            'Food': '🍔',
            'Transport': '🚗',
            'Shopping': '🛍️',
            'Entertainment': '🎬',
            'Bills': '💡',
            'Health': '⚕️',
            'Other': '📦',
            // Income & Salary
            'Salary': '💼',
            'Monthly Salary': '💼',
            'Bonus': '🎉',
            'Freelance': '💻',
            'Investment': '📈',
            'Other Income': '💵'
        };
        return emojiMap[this.category] || (this.type === 'income' ? '💵' : '📦');
    }

    toFirestore() {
        return {
            id: this.id,
            amount: Number(this.amount) || 0,
            category: this.category || 'General',
            description: this.description || '',
            date: this.date,
            type: this.type || 'expense',
            splitWith: Array.isArray(this.splitWith) ? this.splitWith : [],
            createdAt: this.createdAt ? firebase.firestore.Timestamp.fromDate(this.createdAt) : firebase.firestore.FieldValue.serverTimestamp()
        };
    }

    static fromFirestore(doc) {
        const data = doc.data() || {};
        const expense = new Expense(
            data.amount,
            data.category,
            data.description,
            data.date,
            data.type || 'expense'
        );
        expense.id = doc.id || data.id;
        expense.splitWith = Array.isArray(data.splitWith) ? data.splitWith : [];
        expense.createdAt = data.createdAt ? (typeof data.createdAt.toDate === 'function' ? data.createdAt.toDate() : new Date(data.createdAt)) : new Date();
        return expense;
    }
}

/**
 * ExpenseManager Class
 * Handles operations and persistence across Cloud Firestore
 */
class ExpenseManager {
    constructor(user) {
        this.user = user;
        this.db = null;
        if (typeof firebase !== 'undefined' && firebase.apps && firebase.apps.length > 0) {
            try {
                this.db = firebase.firestore();
            } catch (err) {
                console.warn('Firestore initialization failed:', err);
            }
        }
    }

    _getLocalState() {
        const key = `expense_tracker_data_${this.user.uid}`;
        try {
            const raw = localStorage.getItem(key);
            if (raw) return JSON.parse(raw);
        } catch (e) {
            console.error('Error reading localStorage:', e);
        }
        return null;
    }

    _saveLocalState() {
        const key = `expense_tracker_data_${this.user.uid}`;
        try {
            const data = {
                budgets: this.user.budgets || {},
                salaries: this.user.salaries || {},
                employer: this.user.employer || '',
                expenses: this.user.expenses.map(e => ({
                    id: e.id,
                    amount: e.amount,
                    category: e.category,
                    description: e.description,
                    date: e.date,
                    type: e.type || 'expense',
                    splitWith: e.splitWith || [],
                    createdAt: e.createdAt ? e.createdAt.toISOString() : new Date().toISOString()
                }))
            };
            localStorage.setItem(key, JSON.stringify(data));
        } catch (e) {
            console.error('Error saving to localStorage:', e);
        }
    }

    /**
     * Save Monthly Salary / Employment details
     */
    async saveSalary(amount, employer = '', month = null, year = null, payDay = 1) {
        try {
            const now = new Date();
            const salaryMonth = month !== null ? month : now.getMonth();
            const salaryYear = year !== null ? year : now.getFullYear();
            const monthKey = `${salaryYear}-${salaryMonth}`;

            this.user.setSalary(amount, salaryMonth, salaryYear, employer, payDay);

            if (this.db) {
                await this.db.collection('users').doc(this.user.uid).set({
                    salaries: this.user.salaries,
                    employer: this.user.employer,
                    updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                }, { merge: true });
            } else {
                this._saveLocalState();
            }

            return true;
        } catch (error) {
            console.error('Error saving salary to cloud, saving locally:', error);
            this._saveLocalState();
            return true;
        }
    }

    /**
     * Save Budget
     */
    async saveBudget(amount, month = null, year = null) {
        try {
            const now = new Date();
            const budgetMonth = month !== null ? month : now.getMonth();
            const budgetYear = year !== null ? year : now.getFullYear();
            const monthKey = `${budgetYear}-${budgetMonth}`;
            
            this.user.setBudget(amount, budgetMonth, budgetYear);

            if (this.db) {
                await this.db.collection('users').doc(this.user.uid).set({
                    budgets: this.user.budgets,
                    updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                }, { merge: true });
            } else {
                this._saveLocalState();
            }
            return true;
        } catch (error) {
            console.error('Error saving budget:', error);
            this._saveLocalState();
            return true;
        }
    }

    /**
     * Add expense or income transaction
     */
    async addExpense(expenseData) {
        try {
            const expense = new Expense(
                expenseData.amount,
                expenseData.category,
                expenseData.description,
                expenseData.date,
                expenseData.type || 'expense'
            );

            if (expenseData.splitWith && expenseData.splitWith.length > 0) {
                expense.splitBetween(expenseData.splitWith);
            }

            if (this.db) {
                await this.db
                    .collection('users')
                    .doc(this.user.uid)
                    .collection('expenses')
                    .doc(expense.id)
                    .set(expense.toFirestore());
            }

            this.user.addExpense(expense);
            if (!this.db) {
                this._saveLocalState();
            }
            return expense;
        } catch (error) {
            console.error('Error adding transaction to cloud, saving locally:', error);
            const expense = new Expense(
                expenseData.amount,
                expenseData.category,
                expenseData.description,
                expenseData.date,
                expenseData.type || 'expense'
            );
            if (expenseData.splitWith && expenseData.splitWith.length > 0) {
                expense.splitBetween(expenseData.splitWith);
            }
            this.user.addExpense(expense);
            this._saveLocalState();
            return expense;
        }
    }

    /**
     * Delete expense
     */
    async deleteExpense(expenseId) {
        try {
            if (this.db) {
                await this.db
                    .collection('users')
                    .doc(this.user.uid)
                    .collection('expenses')
                    .doc(expenseId)
                    .delete();
            }

            this.user.removeExpense(expenseId);
            if (!this.db) {
                this._saveLocalState();
            }
            return true;
        } catch (error) {
            console.error('Error deleting transaction:', error);
            this.user.removeExpense(expenseId);
            this._saveLocalState();
            return true;
        }
    }

    /**
     * Load user data strictly from Cloud Firestore
     */
    async loadUserData() {
        if (!this.db) {
            console.warn('No Firestore connection found, initializing empty user state');
            this.user.budgets = {};
            this.user.salaries = {};
            this.user.employer = '';
            this.user.expenses = [];
            return true;
        }

        try {
            const userDoc = await this.db.collection('users').doc(this.user.uid).get();
            if (userDoc.exists) {
                const data = userDoc.data() || {};
                this.user.budgets = data.budgets || {};
                this.user.salaries = data.salaries || {};
                this.user.employer = data.employer || '';
            } else {
                // Initialize clean user document in Firestore without any hardcoded values
                await this.db.collection('users').doc(this.user.uid).set({
                    uid: this.user.uid,
                    email: this.user.email || '',
                    displayName: this.user.displayName || '',
                    photoURL: this.user.photoURL || '',
                    budgets: {},
                    salaries: {},
                    employer: '',
                    createdAt: firebase.firestore.FieldValue.serverTimestamp()
                }, { merge: true });
                this.user.budgets = {};
                this.user.salaries = {};
                this.user.employer = '';
            }

            // Load user's actual transactions from Firestore
            const expensesSnapshot = await this.db
                .collection('users')
                .doc(this.user.uid)
                .collection('expenses')
                .get();

            this.user.expenses = [];
            expensesSnapshot.forEach(doc => {
                const expense = Expense.fromFirestore(doc);
                this.user.addExpense(expense);
            });

            return true;
        } catch (error) {
            console.error('Error loading data from Firestore:', error);
            this.user.budgets = {};
            this.user.salaries = {};
            this.user.employer = '';
            this.user.expenses = [];
            return false;
        }
    }

    /**
     * Get spending by category for specific month
     */
    getSpendingByCategory(month = null, year = null) {
        const categoryTotals = {};
        const expenses = (month !== null && year !== null)
            ? this.user.expenses.filter(e => {
                const d = new Date(e.date);
                return d.getMonth() === month && d.getFullYear() === year && e.type !== 'income';
              })
            : this.user.expenses.filter(e => e.type !== 'income');

        expenses.forEach(expense => {
            if (!categoryTotals[expense.category]) {
                categoryTotals[expense.category] = 0;
            }
            categoryTotals[expense.category] += expense.amount;
        });
        return categoryTotals;
    }
}

// Global expose
window.User = User;
window.Budget = Budget;
window.Expense = Expense;
window.ExpenseManager = ExpenseManager;
