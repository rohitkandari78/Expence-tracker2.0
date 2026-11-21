// ==========================================================================
// 3D SPATIAL DASHBOARD ENGINE - EMPLOYEE SALARY & EXPENSE TRACKER
// ==========================================================================

// Global state
let currentUser = null;
let expenseManager = null;
let viewingMonth = new Date().getMonth();
let viewingYear = new Date().getFullYear();
let activeCategoryFilter = null;
let searchQuery = '';
let activeTransactionTypeFilter = 'all'; // 'all', 'expense', 'income'
let currentModalTransactionType = 'expense'; // 'expense' or 'income'

// DOM Elements - Header & User Profile
const signOutBtn = document.getElementById('signOutBtn');
const userPhoto = document.getElementById('userPhoto');
const userName = document.getElementById('userName');
const cardHolderName = document.getElementById('cardHolderName');
const cardBudgetStatus = document.getElementById('cardBudgetStatus');
const storageModeLabel = document.getElementById('storageModeLabel');
const openSalaryModalTopBtn = document.getElementById('openSalaryModalTopBtn');
const headerSalaryText = document.getElementById('headerSalaryText');

// DOM Elements - Titanium Card
const budgetCard = document.getElementById('budgetCard');
const budgetDisplay = document.getElementById('budgetDisplay');
const cardSalaryDisplay = document.getElementById('cardSalaryDisplay');
const cardEmployerDisplay = document.getElementById('cardEmployerDisplay');
const cardSavingsDisplay = document.getElementById('cardSavingsDisplay');
const budgetMonthIndicator = document.getElementById('budgetMonthIndicator');
const editBudgetBtn = document.getElementById('editBudgetBtn');
const editSalaryBtn = document.getElementById('editSalaryBtn');

// DOM Elements - 3D Stat Metrics Grid
const monthlySalaryStat = document.getElementById('monthlySalaryStat');
const employerBadge = document.getElementById('employerBadge');
const totalSpentEl = document.getElementById('totalSpent');
const spentPercentageBadge = document.getElementById('spentPercentageBadge');
const remainingEl = document.getElementById('remaining');
const remainingStatusBadge = document.getElementById('remainingStatusBadge');
const dailyAverageSpent = document.getElementById('dailyAverageSpent');
const paydayCounter = document.getElementById('paydayCounter');

// DOM Elements - 50/30/20 Rule Advisor
const needsPercentLabel = document.getElementById('needsPercentLabel');
const needsProgressBar = document.getElementById('needsProgressBar');
const needsSpentText = document.getElementById('needsSpentText');
const wantsPercentLabel = document.getElementById('wantsPercentLabel');
const wantsProgressBar = document.getElementById('wantsProgressBar');
const wantsSpentText = document.getElementById('wantsSpentText');
const savingsPercentLabel = document.getElementById('savingsPercentLabel');
const savingsProgressBar = document.getElementById('savingsProgressBar');
const savingsRetainedText = document.getElementById('savingsRetainedText');

// DOM Elements - Progress Bar
const progressFill = document.getElementById('progressFill');
const progressPercentLabel = document.getElementById('progressPercentLabel');

// DOM Elements - Modals
const budgetModal = document.getElementById('budgetModal');
const budgetInput = document.getElementById('budgetInput');
const saveBudgetBtn = document.getElementById('saveBudgetBtn');

const salaryModal = document.getElementById('salaryModal');
const salaryInput = document.getElementById('salaryInput');
const employerInput = document.getElementById('employerInput');
const paydayInput = document.getElementById('paydayInput');
const autoSalaryCreditCheckbox = document.getElementById('autoSalaryCreditCheckbox');
const saveSalaryBtn = document.getElementById('saveSalaryBtn');

const expenseModal = document.getElementById('expenseModal');
const expenseModalTitle = document.getElementById('expenseModalTitle');
const saveExpenseBtn = document.getElementById('saveExpenseBtn');
const saveBtnLabelText = document.getElementById('saveBtnLabelText');
const typeSwitchExpense = document.getElementById('typeSwitchExpense');
const typeSwitchIncome = document.getElementById('typeSwitchIncome');
const expenseAmount = document.getElementById('expenseAmount');
const expenseCategory = document.getElementById('expenseCategory');
const expenseDescription = document.getElementById('expenseDescription');
const expenseDate = document.getElementById('expenseDate');
const splitCardOptionWrapper = document.getElementById('splitCardOptionWrapper');
const splitExpenseCheckbox = document.getElementById('splitExpenseCheckbox');
const splitSection = document.getElementById('splitSection');
const splitPeople = document.getElementById('splitPeople');
const splitPreview = document.getElementById('splitPreview');

// DOM Elements - Actions, Toolbar & List
const addExpenseBtn = document.getElementById('addExpenseBtn');
const expensesList = document.getElementById('expensesList');
const emptyState = document.getElementById('emptyState');
const expenseCountBadge = document.getElementById('expenseCountBadge');
const currentMonthBadge = document.getElementById('currentMonthBadge');
const prevMonthBtn = document.getElementById('prevMonthBtn');
const nextMonthBtn = document.getElementById('nextMonthBtn');
const todayBtn = document.getElementById('todayBtn');
const categoryGrid = document.getElementById('categoryGrid');
const expenseSearchInput = document.getElementById('expenseSearchInput');

// Category sets (Canonical 9 categories with 50/30/20 mapping)
const EXPENSE_CATEGORIES = [
    { value: 'Rent & Housing', label: '🏠 Rent & Housing' },
    { value: 'Groceries & Food', label: '🛒 Groceries & Food' },
    { value: 'Transport & Fuel', label: '🚗 Transport & Fuel' },
    { value: 'Utilities & Bills', label: '💡 Utilities & Bills' },
    { value: 'Health & Wellness', label: '⚕️ Health & Wellness' },
    { value: 'Dining Out', label: '🍽️ Dining Out' },
    { value: 'Shopping', label: '🛍️ Shopping' },
    { value: 'Entertainment', label: '🎬 Entertainment' },
    { value: 'Other Expenses', label: '📦 Other Expenses' }
];

const INCOME_CATEGORIES = [
    { value: 'Salary', label: '💼 Monthly In-Hand Salary' },
    { value: 'Bonus', label: '🎉 Performance Bonus & Incentive' },
    { value: 'Freelance', label: '💻 Freelance & Side Income' },
    { value: 'Investment', label: '📈 Dividend & Stock Returns' },
    { value: 'Other Income', label: '💵 Reimbursement / Other Credit' }
];

// 50/30/20 Category Normalization & Bucket Mapping
const NEEDS_CATEGORIES = [
    'Rent & Housing',
    'Groceries & Food',
    'Transport & Fuel',
    'Utilities & Bills',
    'Health & Wellness'
];

const WANTS_CATEGORIES = [
    'Dining Out',
    'Shopping',
    'Entertainment',
    'Other Expenses'
];

function normalizeCategory(category) {
    if (!category) return 'Other Expenses';
    const c = category.trim();

    // Needs category aliases (including legacy categories)
    if (c === 'Rent & Housing' || c === 'Rent' || c === 'Housing') return 'Rent & Housing';
    if (c === 'Groceries & Food' || c === 'Food & Dining' || c === 'Food' || c === 'Groceries' || c === 'Food & Groceries') return 'Groceries & Food';
    if (c === 'Transport & Fuel' || c === 'Transport' || c === 'Fuel') return 'Transport & Fuel';
    if (c === 'Utilities & Bills' || c === 'Bills' || c === 'Utilities' || c === 'Utilities & Rent Bills') return 'Utilities & Bills';
    if (c === 'Health & Wellness' || c === 'Health' || c === 'Medical' || c === 'Health & Medical') return 'Health & Wellness';

    // Wants category aliases
    if (c === 'Dining Out' || c === 'Dining' || c === 'Restaurant') return 'Dining Out';
    if (c === 'Shopping' || c === 'Shopping & Gadgets') return 'Shopping';
    if (c === 'Entertainment' || c === 'Entertainment & Outings' || c === 'Movies') return 'Entertainment';
    if (c === 'Other Expenses' || c === 'Other') return 'Other Expenses';

    return c;
}

function isNeedsCategory(category) {
    const norm = normalizeCategory(category);
    return NEEDS_CATEGORIES.includes(norm);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    setTodayDate();
    init3DTiltCards();
    initAmbientCanvas();
    initAiAssistant();
});

/**
 * Initialize Application (Strict Firebase Authentication)
 */
function initializeApp() {
    // Clear any previous demo/guest mode flags
    localStorage.removeItem('expense_tracker_guest_mode');

    if (typeof auth !== 'undefined' && auth.onAuthStateChanged) {
        auth.onAuthStateChanged(async (user) => {
            if (user) {
                await handleUserSignIn(user);
                // Hide auth guard overlay once user data is loaded and rendered
                const overlay = document.getElementById('authGuardOverlay');
                if (overlay) overlay.classList.add('hidden');
            } else {
                console.log('No active authenticated session, redirecting to login...');
                window.location.replace('../login/login.html');
            }
        });
    } else {
        window.location.replace('../login/login.html');
    }
}

/**
 * Handle user sign in
 */
async function handleUserSignIn(userInstance) {
    try {
        const displayName = (userInstance.displayName && userInstance.displayName.trim()) || 
                            (userInstance.email ? userInstance.email.split('@')[0] : 'User');

        currentUser = new User(
            userInstance.uid,
            userInstance.email,
            displayName,
            userInstance.photoURL || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
            false
        );
        if (storageModeLabel) {
            storageModeLabel.textContent = 'Cloud Synced';
        }

        expenseManager = new ExpenseManager(currentUser);
        await expenseManager.loadUserData();

        updateUserProfile();
        renderExpensesForViewingMonth();

        showToast(`Welcome back, ${displayName}!`, 'success');
    } catch (error) {
        console.error('Error during sign in initialization:', error);
        showToast('Error loading financial profile from Cloud.', 'error');
    }
}

/**
 * Update user profile in header and card
 */
function updateUserProfile() {
    const avatarUrl = currentUser.photoURL || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80';
    const rawName = currentUser.displayName;
    const name = (rawName && rawName !== 'Employee User' && rawName !== 'Demo User') ? rawName : 'Not set';

    if (userPhoto) userPhoto.src = avatarUrl;
    if (userName) userName.textContent = name;
    if (cardHolderName) cardHolderName.textContent = name;
}

/**
 * Update dashboard metrics for specific month
 */
function updateDashboardForMonth(month, year) {
    const salary = currentUser.getSalary(month, year);
    const employer = currentUser.getEmployer(month, year);
    const totalIncome = currentUser.getTotalIncome(month, year);
    const totalSpent = currentUser.getTotalSpent(month, year);
    const netSavings = currentUser.getNetSavings(month, year);
    const savingsPercent = currentUser.getSavingsPercentage(month, year);
    const budget = currentUser.getBudget(month, year);

    // Header Quick Salary Info
    if (headerSalaryText) {
        headerSalaryText.textContent = (totalIncome > 0 && isFinite(totalIncome)) 
            ? formatCurrency(salary > 0 ? salary : totalIncome) 
            : 'Set Salary';
    }

    // Card Displays
    budgetDisplay.textContent = formatCurrency(budget);
    cardSalaryDisplay.textContent = (totalIncome > 0 && isFinite(totalIncome))
        ? formatCurrency(salary > 0 ? salary : totalIncome)
        : formatCurrency(0);
    cardEmployerDisplay.textContent = employer || 'Not set';
    cardSavingsDisplay.textContent = formatCurrency(netSavings);

    if (netSavings >= 0) {
        cardSavingsDisplay.className = 'strip-value savings-positive';
    } else {
        cardSavingsDisplay.className = 'strip-value';
        cardSavingsDisplay.style.color = '#f43f5e';
    }

    // Metrics Grid: Stat 1 - Monthly Salary & Inflow
    if (monthlySalaryStat) {
        monthlySalaryStat.textContent = formatCurrency(totalIncome);
    }
    if (employerBadge) {
        employerBadge.textContent = employer ? `${employer} • In-Hand` : 'Not set';
    }

    // Stat 2 - Total Expenses Spent
    totalSpentEl.textContent = formatCurrency(totalSpent);
    if (spentPercentageBadge) {
        if (totalIncome > 0 && isFinite(totalIncome)) {
            const spentOfIncome = ((totalSpent / totalIncome) * 100).toFixed(1);
            spentPercentageBadge.textContent = `${spentOfIncome}% of monthly salary spent`;
        } else {
            spentPercentageBadge.textContent = 'Set your salary first';
        }
    }

    // Stat 3 - Net In-Pocket Savings
    remainingEl.textContent = formatCurrency(netSavings);
    if (remainingStatusBadge) {
        if (!totalIncome || totalIncome <= 0 || !isFinite(totalIncome)) {
            remainingStatusBadge.textContent = 'Set your salary first';
            remainingStatusBadge.style.color = 'var(--text-dim)';
        } else if (netSavings < 0) {
            remainingStatusBadge.textContent = 'Deficit: Overspending Salary ⚠️';
            remainingStatusBadge.style.color = '#f43f5e';
        } else if (savingsPercent >= 40) {
            remainingStatusBadge.textContent = `${savingsPercent.toFixed(1)}% Saved • High Saver 🌟`;
            remainingStatusBadge.style.color = '#34d399';
        } else {
            remainingStatusBadge.textContent = `${savingsPercent.toFixed(1)}% Saved • On Track ✨`;
            remainingStatusBadge.style.color = '#38bdf8';
        }
    }

    // Card Financial Health Tag
    if (cardBudgetStatus) {
        if (netSavings < 0 && totalIncome > 0) {
            cardBudgetStatus.textContent = 'SALARY DEFICIT';
            cardBudgetStatus.style.color = '#f43f5e';
            cardBudgetStatus.style.background = 'rgba(244, 63, 94, 0.15)';
            cardBudgetStatus.style.borderColor = 'rgba(244, 63, 94, 0.3)';
        } else {
            cardBudgetStatus.textContent = 'HEALTHY SAVINGS';
            cardBudgetStatus.style.color = '#34d399';
            cardBudgetStatus.style.background = 'rgba(16, 185, 129, 0.15)';
            cardBudgetStatus.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        }
    }

    // Stat 4 - Average spend per day this month
    const now = new Date();
    const isCurrentMonth = month === now.getMonth() && year === now.getFullYear();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysPassed = isCurrentMonth ? Math.max(1, now.getDate()) : daysInMonth;

    const avgSpendPerDay = (totalSpent > 0 && isFinite(totalSpent)) ? (totalSpent / daysPassed) : 0;
    if (dailyAverageSpent) {
        dailyAverageSpent.textContent = `${formatCurrency(avgSpendPerDay)} / day`;
    }
    if (paydayCounter) {
        if (isCurrentMonth) {
            paydayCounter.textContent = `${daysPassed} of ${daysInMonth} days passed`;
        } else {
            paydayCounter.textContent = `Completed month (${daysInMonth} days)`;
        }
    }

    // Month Indicator text
    const viewingDate = new Date(year, month);
    const monthName = viewingDate.toLocaleString('default', { month: 'long', year: 'numeric' });

    if (isCurrentMonth) {
        budgetMonthIndicator.textContent = '(Current Month)';
        budgetMonthIndicator.style.color = '#38bdf8';
    } else {
        budgetMonthIndicator.textContent = `(${monthName})`;
        budgetMonthIndicator.style.color = 'var(--text-dim)';
    }

    // Budget Utilization Progress Bar
    const budgetPercent = (budget > 0 && isFinite(budget)) ? (totalSpent / budget) * 100 : 0;
    const cappedPercent = Math.min(budgetPercent, 100);
    progressFill.style.width = cappedPercent + '%';
    if (progressPercentLabel) {
        progressPercentLabel.textContent = budget > 0 ? `${budgetPercent.toFixed(0)}%` : '-';
    }

    if (totalSpent > budget && budget > 0) {
        progressFill.style.background = 'linear-gradient(90deg, #f43f5e 0%, #e11d48 100%)';
        progressFill.style.boxShadow = '0 0 15px rgba(244, 63, 94, 0.7)';
    } else {
        progressFill.style.background = 'linear-gradient(90deg, #6366f1 0%, #38bdf8 50%, #818cf8 100%)';
        progressFill.style.boxShadow = '0 0 12px rgba(99, 102, 241, 0.6)';
    }

    // Update 50/30/20 Salary Health Advisor
    updateSalaryAdvisor(month, year, totalIncome, totalSpent, netSavings);

    // Update Category Breakdown Grid
    renderCategoryBreakdown(month, year);
}

/**
 * 50/30/20 Salary Allocation Rule Calculator
 */
function updateSalaryAdvisor(month, year, income, totalSpent, netSavings) {
    if (!needsPercentLabel || !wantsPercentLabel || !savingsPercentLabel) return;

    if (!income || income <= 0 || !isFinite(income)) {
        needsPercentLabel.textContent = '-';
        wantsPercentLabel.textContent = '-';
        savingsPercentLabel.textContent = '-';
        needsProgressBar.style.width = '0%';
        wantsProgressBar.style.width = '0%';
        savingsProgressBar.style.width = '0%';
        needsSpentText.textContent = 'Set your salary first';
        wantsSpentText.textContent = 'Set your salary first';
        savingsRetainedText.textContent = 'Set your salary first';
        return;
    }

    const monthExpenses = currentUser.getExpensesForMonth(month, year).filter(e => e.type !== 'income');

    let needsTotal = 0;
    let wantsTotal = 0;

    monthExpenses.forEach(exp => {
        if (isNeedsCategory(exp.category)) {
            needsTotal += exp.amount;
        } else {
            wantsTotal += exp.amount;
        }
    });

    // Savings = salary minus total expenses
    const savingsAmount = income - totalSpent;

    const needsRatio = (needsTotal / income) * 100;
    const wantsRatio = (wantsTotal / income) * 100;
    const savingsRatio = Math.max(0, (savingsAmount / income) * 100);

    needsPercentLabel.textContent = isFinite(needsRatio) ? `${needsRatio.toFixed(1)}%` : '0%';
    needsProgressBar.style.width = `${Math.min(isFinite(needsRatio) ? needsRatio : 0, 100)}%`;
    needsSpentText.textContent = `${formatCurrency(needsTotal)} spent`;

    wantsPercentLabel.textContent = isFinite(wantsRatio) ? `${wantsRatio.toFixed(1)}%` : '0%';
    wantsProgressBar.style.width = `${Math.min(isFinite(wantsRatio) ? wantsRatio : 0, 100)}%`;
    wantsSpentText.textContent = `${formatCurrency(wantsTotal)} spent`;

    savingsPercentLabel.textContent = isFinite(savingsRatio) ? `${savingsRatio.toFixed(1)}%` : '0%';
    savingsProgressBar.style.width = `${Math.min(isFinite(savingsRatio) ? savingsRatio : 0, 100)}%`;
    savingsRetainedText.textContent = `${formatCurrency(savingsAmount)} retained`;
}

/**
 * Render Category Breakdown Panel (Expenses only)
 */
function renderCategoryBreakdown(month, year) {
    if (!categoryGrid) return;
    categoryGrid.innerHTML = '';

    const categories = [
        { name: 'Rent & Housing', emoji: '🏠' },
        { name: 'Groceries & Food', emoji: '🛒' },
        { name: 'Transport & Fuel', emoji: '🚗' },
        { name: 'Utilities & Bills', emoji: '💡' },
        { name: 'Health & Wellness', emoji: '⚕️' },
        { name: 'Dining Out', emoji: '🍽️' },
        { name: 'Shopping', emoji: '🛍️' },
        { name: 'Entertainment', emoji: '🎬' },
        { name: 'Other Expenses', emoji: '📦' }
    ];

    const monthExpenses = currentUser.getExpensesForMonth(month, year).filter(e => e.type !== 'income');
    const totals = {};
    let grandTotal = 0;

    monthExpenses.forEach(e => {
        const norm = normalizeCategory(e.category);
        totals[norm] = (totals[norm] || 0) + e.amount;
        grandTotal += e.amount;
    });

    categories.forEach(cat => {
        const catAmount = totals[cat.name] || 0;
        const percent = grandTotal > 0 ? (catAmount / grandTotal) * 100 : 0;
        const isActive = activeCategoryFilter === cat.name;

        const chip = document.createElement('div');
        chip.className = `category-chip-card ${isActive ? 'active-filter' : ''}`;
        chip.title = `Click to filter by ${cat.name}`;

        chip.innerHTML = `
            <div class="chip-header">
                <span class="chip-emoji">${cat.emoji}</span>
                <span class="chip-name">${cat.name}</span>
            </div>
            <div class="chip-amount">${formatCurrency(catAmount)}</div>
            <div style="margin-top: 6px; height: 3px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;">
                <div style="width: ${percent}%; height: 100%; background: #818cf8; border-radius: 2px;"></div>
            </div>
        `;

        chip.addEventListener('click', () => {
            activeCategoryFilter = (activeCategoryFilter === cat.name) ? null : cat.name;
            renderExpensesForViewingMonth();
        });

        categoryGrid.appendChild(chip);
    });
}

/**
 * Render transactions for viewing month
 */
function renderExpensesForViewingMonth() {
    expensesList.innerHTML = '';
    updateDashboardForMonth(viewingMonth, viewingYear);

    // Update month badge text dynamically
    const viewingDate = new Date(viewingYear, viewingMonth);
    const monthName = viewingDate.toLocaleString('default', { month: 'long', year: 'numeric' });
    const now = new Date();
    const isCurrentMonth = viewingMonth === now.getMonth() && viewingYear === now.getFullYear();
    currentMonthBadge.textContent = isCurrentMonth ? `${monthName} - Current` : monthName;

    todayBtn.style.display = isCurrentMonth ? 'none' : 'inline-flex';

    // Get all transactions for viewing month
    let items = currentUser.getExpensesForMonth(viewingMonth, viewingYear);

    // Filter by Transaction Type (All, Expense, Income)
    if (activeTransactionTypeFilter === 'expense') {
        items = items.filter(e => e.type !== 'income');
    } else if (activeTransactionTypeFilter === 'income') {
        items = items.filter(e => e.type === 'income');
    }

    // Filter by Category using normalized category
    if (activeCategoryFilter) {
        items = items.filter(e => normalizeCategory(e.category) === activeCategoryFilter);
    }

    // Search Query Filter
    if (searchQuery.trim().length > 0) {
        const q = searchQuery.toLowerCase().trim();
        items = items.filter(e => 
            e.description.toLowerCase().includes(q) || 
            normalizeCategory(e.category).toLowerCase().includes(q)
        );
    }

    if (expenseCountBadge) {
        expenseCountBadge.textContent = items.length;
    }

    if (items.length === 0) {
        emptyState.style.display = 'block';
        const emptyTitle = emptyState.querySelector('h4');
        if (emptyTitle) {
            emptyTitle.textContent = `No ${activeTransactionTypeFilter !== 'all' ? activeTransactionTypeFilter : ''} transactions for ${monthName}`;
        }
        return;
    }

    emptyState.style.display = 'none';

    // Sort newest first
    const sorted = [...items].sort((a, b) => new Date(b.date) - new Date(a.date));

    sorted.forEach(item => {
        const card = createTransactionCard(item);
        expensesList.appendChild(card);
    });
}

/**
 * Create 3D Transaction Card (Expense or Income/Salary)
 */
function createTransactionCard(item) {
    const card = document.createElement('div');
    const isIncome = item.isIncome();
    card.className = `expense-item ${isIncome ? 'income-item' : ''}`;

    const amountPerPerson = item.isSplit() ? item.getAmountPerPerson() : item.amount;
    const signPrefix = isIncome ? '+' : '-';
    const amountClass = isIncome ? 'income-amount' : '';
    const safeDesc = escapeHtml(item.description || '');
    const safeCat = escapeHtml(item.category || '');
    const safeSplit = item.isSplit() ? escapeHtml((item.splitWith || []).join(', ')) : '';

    card.innerHTML = `
        <div class="expense-info">
            <div class="expense-category-orb">
                ${item.getCategoryEmoji()}
            </div>
            <div class="expense-header">
                <span class="expense-description">${safeDesc}</span>
                <div class="expense-meta">
                    <span class="expense-date">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                        </svg>
                        ${item.getFormattedDate()}
                    </span>
                    <span class="expense-category-text">• ${safeCat}</span>
                    ${isIncome ? '<span class="credit-badge">🟢 Salary / Credit</span>' : ''}
                </div>
            </div>
        </div>
        <div class="expense-amount-section">
            <div class="expense-amount-block">
                <div class="expense-amount ${amountClass}">
                    ${signPrefix}${formatCurrency(item.amount)}
                </div>
                ${item.isSplit() ? `
                    <div class="split-badge" title="Split with ${safeSplit}">
                        <span>🤝 ${formatCurrency(amountPerPerson)}/ea</span>
                    </div>
                ` : ''}
            </div>
            <div class="expense-actions">
                <button class="btn-delete" title="Delete Transaction" data-expense-id="${item.id}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;

    const delBtn = card.querySelector('.btn-delete');
    if (delBtn) {
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteExpense(item.id);
        });
    }

    return card;
}

/**
 * Setup Event Listeners
 */
function setupEventListeners() {
    if (signOutBtn) signOutBtn.addEventListener('click', signOut);

    // Salary Modal
    if (openSalaryModalTopBtn) openSalaryModalTopBtn.addEventListener('click', openSalaryModal);
    if (editSalaryBtn) editSalaryBtn.addEventListener('click', openSalaryModal);
    if (saveSalaryBtn) saveSalaryBtn.addEventListener('click', saveSalary);

    // Budget Modal
    if (editBudgetBtn) editBudgetBtn.addEventListener('click', openBudgetModal);
    if (saveBudgetBtn) saveBudgetBtn.addEventListener('click', saveBudget);

    // Expense / Income Modal
    if (addExpenseBtn) addExpenseBtn.addEventListener('click', () => openExpenseModal('expense'));
    if (saveExpenseBtn) saveExpenseBtn.addEventListener('click', saveTransaction);

    // Transaction Type Switcher in Modal
    if (typeSwitchExpense) {
        typeSwitchExpense.addEventListener('click', () => setModalTransactionType('expense'));
    }
    if (typeSwitchIncome) {
        typeSwitchIncome.addEventListener('click', () => setModalTransactionType('income'));
    }

    // Split expense controls
    if (splitExpenseCheckbox) splitExpenseCheckbox.addEventListener('change', toggleSplitSection);
    if (splitPeople) splitPeople.addEventListener('input', updateSplitPreview);
    if (expenseAmount) expenseAmount.addEventListener('input', updateSplitPreview);

    // Month Navigation
    if (prevMonthBtn) prevMonthBtn.addEventListener('click', goToPrevMonth);
    if (nextMonthBtn) nextMonthBtn.addEventListener('click', goToNextMonth);
    if (todayBtn) todayBtn.addEventListener('click', goToToday);

    // Search bar
    if (expenseSearchInput) {
        expenseSearchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value;
            renderExpensesForViewingMonth();
        });
    }

    // Transaction Type Filter Tabs
    document.querySelectorAll('.tx-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.tx-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            activeTransactionTypeFilter = this.getAttribute('data-tx-filter') || 'all';
            renderExpensesForViewingMonth();
        });
    });

    setupModalControls();
}

/**
 * Open Salary Modal
 */
function openSalaryModal() {
    const currentSalary = currentUser.getSalary(viewingMonth, viewingYear);
    const currentEmployer = currentUser.getEmployer(viewingMonth, viewingYear);

    salaryInput.value = currentSalary || '';
    employerInput.value = currentEmployer || '';
    paydayInput.value = 1;

    salaryModal.classList.add('active');
    salaryInput.focus();
}

/**
 * Save Salary Profile
 */
async function saveSalary() {
    const rawAmount = salaryInput.value.trim();
    const amount = parseFloat(rawAmount);
    const employer = employerInput.value.trim().substring(0, 50) || 'Not set';
    const payDay = parseInt(paydayInput.value) || 1;

    if (!rawAmount || isNaN(amount) || !isFinite(amount) || amount <= 0) {
        showToast('Please enter a valid positive in-hand salary amount', 'error');
        return;
    }
    if (payDay < 1 || payDay > 31) {
        showToast('Payday must be between 1 and 31', 'error');
        return;
    }

    try {
        saveSalaryBtn.disabled = true;
        const topEl = saveSalaryBtn.querySelector('.btn-3d-top');
        if (topEl) topEl.innerHTML = '<span class="loading"></span> Saving Salary...';

        await expenseManager.saveSalary(amount, employer, viewingMonth, viewingYear, payDay);

        // Auto log as Salary Credit transaction if checked
        if (autoSalaryCreditCheckbox.checked) {
            const y = viewingYear;
            const m = String(viewingMonth + 1).padStart(2, '0');
            const d = String(Math.min(payDay, 28)).padStart(2, '0');
            const salaryDate = `${y}-${m}-${d}`;

            // Check if already logged this month to avoid duplicates
            const hasExisting = currentUser.expenses.some(e => 
                e.type === 'income' && 
                (e.category === 'Salary' || e.category === 'Monthly Salary') &&
                new Date(e.date).getMonth() === viewingMonth &&
                new Date(e.date).getFullYear() === viewingYear
            );

            if (!hasExisting) {
                await expenseManager.addExpense({
                    amount,
                    category: 'Salary',
                    description: `Monthly In-Hand Salary (${employer})`,
                    date: salaryDate,
                    type: 'income',
                    splitWith: []
                });
            }
        }

        renderExpensesForViewingMonth();
        closeModal(salaryModal);
        showToast(`Monthly salary profile saved for ${employer}!`, 'success');
    } catch (error) {
        console.error('Error saving salary:', error);
        showToast(`Could not save salary: ${error.message || 'Firestore write error'}`, 'error');
    } finally {
        saveSalaryBtn.disabled = false;
        const topEl = saveSalaryBtn.querySelector('.btn-3d-top');
        if (topEl) topEl.textContent = 'Save Salary Profile';
    }
}

/**
 * Open Budget Modal
 */
function openBudgetModal() {
    const currentBudget = currentUser.getBudget(viewingMonth, viewingYear);
    budgetInput.value = currentBudget || '';

    const viewingDate = new Date(viewingYear, viewingMonth);
    const monthName = viewingDate.toLocaleString('default', { month: 'long', year: 'numeric' });
    const modalTitle = document.querySelector('#budgetModal .modal-header h3');
    if (modalTitle) modalTitle.textContent = `Set Budget for ${monthName}`;

    budgetModal.classList.add('active');
    budgetInput.focus();
}

/**
 * Save Budget
 */
async function saveBudget() {
    const rawAmount = budgetInput.value.trim();
    const amount = parseFloat(rawAmount);

    if (!rawAmount || isNaN(amount) || !isFinite(amount) || amount <= 0) {
        showToast('Please enter a valid positive budget amount', 'error');
        return;
    }

    try {
        saveBudgetBtn.disabled = true;
        const topEl = saveBudgetBtn.querySelector('.btn-3d-top');
        if (topEl) topEl.innerHTML = '<span class="loading"></span> Saving...';

        await expenseManager.saveBudget(amount, viewingMonth, viewingYear);
        renderExpensesForViewingMonth();
        closeModal(budgetModal);

        const viewingDate = new Date(viewingYear, viewingMonth);
        const monthName = viewingDate.toLocaleString('default', { month: 'long', year: 'numeric' });
        showToast(`Budget for ${monthName} saved successfully!`, 'success');
    } catch (error) {
        console.error('Error saving budget:', error);
        showToast(`Could not save budget: ${error.message || 'Firestore write error'}`, 'error');
    } finally {
        saveBudgetBtn.disabled = false;
        const topEl = saveBudgetBtn.querySelector('.btn-3d-top');
        if (topEl) topEl.textContent = 'Save Budget';
    }
}

/**
 * Open Transaction Modal (Expense or Income)
 */
function openExpenseModal(initialType = 'expense') {
    setModalTransactionType(initialType);
    resetExpenseForm();
    expenseModal.classList.add('active');
    expenseAmount.focus();
}

/**
 * Switch modal between Expense and Income modes
 */
function setModalTransactionType(type) {
    currentModalTransactionType = type;

    if (type === 'income') {
        typeSwitchIncome.classList.add('active');
        typeSwitchExpense.classList.remove('active');
        expenseModalTitle.textContent = 'Record Salary & Income Credit 🟢';
        saveBtnLabelText.textContent = 'Save Income Credit';
        if (splitCardOptionWrapper) splitCardOptionWrapper.style.display = 'none';

        // Populate Income categories
        populateCategoryDropdown(INCOME_CATEGORIES);
        expenseDescription.placeholder = 'e.g. October Salary Credited, Bonus, Freelance';
    } else {
        typeSwitchExpense.classList.add('active');
        typeSwitchIncome.classList.remove('active');
        expenseModalTitle.textContent = 'Record Expense (Spent) 🔴';
        saveBtnLabelText.textContent = 'Save Expense';
        if (splitCardOptionWrapper) splitCardOptionWrapper.style.display = 'block';

        // Populate Expense categories
        populateCategoryDropdown(EXPENSE_CATEGORIES);
        expenseDescription.placeholder = 'e.g. Team Lunch, Apartment Rent, Metro Card';
    }
}

function populateCategoryDropdown(categories) {
    expenseCategory.innerHTML = '<option value="">Select category</option>';
    categories.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat.value;
        opt.textContent = cat.label;
        expenseCategory.appendChild(opt);
    });
}

/**
 * Save Transaction (Expense or Income)
 */
async function saveTransaction() {
    const rawAmount = expenseAmount.value.trim();
    const amount = parseFloat(rawAmount);
    const category = expenseCategory.value;
    let description = expenseDescription.value.trim();
    const date = expenseDate.value;

    if (!rawAmount || isNaN(amount) || !isFinite(amount) || amount <= 0) {
        showToast('Please enter a valid positive amount', 'error');
        return;
    }
    if (!category) {
        showToast('Please select a category', 'error');
        return;
    }
    if (!description) {
        showToast('Please enter a description', 'error');
        return;
    }
    if (description.length > 100) {
        description = description.substring(0, 100);
    }
    if (!date) {
        showToast('Please select a date', 'error');
        return;
    }

    try {
        saveExpenseBtn.disabled = true;
        const topEl = saveExpenseBtn.querySelector('.btn-3d-top');
        if (topEl) topEl.innerHTML = '<span class="loading"></span> Recording...';

        const transactionData = {
            amount,
            category,
            description,
            date,
            type: currentModalTransactionType,
            splitWith: []
        };

        if (currentModalTransactionType === 'expense' && splitExpenseCheckbox.checked && splitPeople.value.trim()) {
            transactionData.splitWith = splitPeople.value
                .split(',')
                .map(name => name.trim().substring(0, 30))
                .filter(name => name.length > 0);
        }

        await expenseManager.addExpense(transactionData);

        // Switch viewing month to transaction date
        const expDateObj = new Date(date);
        viewingMonth = expDateObj.getMonth();
        viewingYear = expDateObj.getFullYear();

        renderExpensesForViewingMonth();
        closeModal(expenseModal);

        const msg = currentModalTransactionType === 'income' 
            ? 'Salary / Income credit recorded successfully! 💼' 
            : 'Expense recorded successfully!';
        showToast(msg, 'success');
    } catch (error) {
        console.error('Error saving transaction:', error);
        showToast(`Could not record transaction: ${error.message || 'Firestore write error'}`, 'error');
    } finally {
        saveExpenseBtn.disabled = false;
        const topEl = saveExpenseBtn.querySelector('.btn-3d-top');
        if (topEl) topEl.textContent = currentModalTransactionType === 'income' ? 'Save Income Credit' : 'Save Expense';
    }
}

/**
 * Delete Expense/Transaction
 */
async function deleteExpense(expenseId) {
    if (!confirm('Are you sure you want to remove this transaction?')) return;

    try {
        await expenseManager.deleteExpense(expenseId);
        renderExpensesForViewingMonth();
        showToast('Transaction removed', 'success');
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showToast(`Could not remove transaction: ${error.message || 'Firestore error'}`, 'error');
    }
}

/**
 * Split section toggle & preview
 */
function toggleSplitSection() {
    if (splitExpenseCheckbox.checked) {
        splitSection.style.display = 'block';
        splitPeople.focus();
    } else {
        splitSection.style.display = 'none';
        splitPeople.value = '';
        splitPreview.innerHTML = '';
    }
}

function updateSplitPreview() {
    if (!splitExpenseCheckbox.checked || !splitPeople.value.trim()) {
        splitPreview.innerHTML = '';
        return;
    }

    const amount = parseFloat(expenseAmount.value) || 0;
    const people = splitPeople.value
        .split(',')
        .map(name => name.trim())
        .filter(name => name.length > 0);

    if (people.length === 0 || amount === 0) {
        splitPreview.innerHTML = '';
        return;
    }

    const totalCount = people.length + 1;
    const perPerson = amount / totalCount;

    splitPreview.innerHTML = `
        <p><strong>Total Group:</strong> ${totalCount} people (You + ${people.join(', ')})</p>
        <p><strong>Each Share:</strong> ${formatCurrency(perPerson)}</p>
        <p><strong>Your Contribution:</strong> ${formatCurrency(perPerson)}</p>
    `;
}

/**
 * Modal controls
 */
function setupModalControls() {
    document.querySelectorAll('.modal-close, [data-close-modal]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const modal = this.closest('.modal');
            if (modal) closeModal(modal);
        });
    });
}

function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove('active');
    if (modal === expenseModal) resetExpenseForm();
}

function resetExpenseForm() {
    expenseAmount.value = '';
    expenseCategory.value = '';
    expenseDescription.value = '';
    expenseDate.value = getTodayDate();
    splitExpenseCheckbox.checked = false;
    splitPeople.value = '';
    splitSection.style.display = 'none';
    splitPreview.innerHTML = '';
}

function setTodayDate() {
    if (expenseDate) expenseDate.value = getTodayDate();
}

function getTodayDate() {
    return new Date().toISOString().split('T')[0];
}

function formatCurrency(amount) {
    return '₹' + Number(amount || 0).toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, (m) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    }[m]));
}

/**
 * Sign Out
 */
async function signOut() {
    if (!confirm('Are you sure you want to log out?')) return;

    try {
        localStorage.removeItem('expense_tracker_guest_mode');
        if (typeof auth !== 'undefined' && auth.signOut) {
            await auth.signOut();
        }
        window.location.replace('../login/login.html');
    } catch (error) {
        console.error('Sign out error:', error);
        window.location.replace('../login/login.html');
    }
}

/**
 * Month Navigation
 */
function goToPrevMonth() {
    viewingMonth--;
    if (viewingMonth < 0) {
        viewingMonth = 11;
        viewingYear--;
    }
    renderExpensesForViewingMonth();
}

function goToNextMonth() {
    viewingMonth++;
    if (viewingMonth > 11) {
        viewingMonth = 0;
        viewingYear++;
    }
    renderExpensesForViewingMonth();
}

function goToToday() {
    const now = new Date();
    viewingMonth = now.getMonth();
    viewingYear = now.getFullYear();
    renderExpensesForViewingMonth();
}

/**
 * 3D Physics Tilt for Cards
 */
function init3DTiltCards() {
    if (budgetCard) {
        budgetCard.addEventListener('mousemove', (e) => {
            const rect = budgetCard.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -12;
            const rotateY = ((x - centerX) / centerX) * 12;

            budgetCard.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.02, 1.02, 1.02)`;
            budgetCard.style.setProperty('--mouse-x', `${(x / rect.width) * 100}%`);
            budgetCard.style.setProperty('--mouse-y', `${(y / rect.height) * 100}%`);
        });

        budgetCard.addEventListener('mouseleave', () => {
            budgetCard.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        });
    }

    document.querySelectorAll('.stat-3d-card, .salary-advisor-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -6;
            const rotateY = ((x - centerX) / centerX) * 6;

            card.style.transform = `perspective(900px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.01, 1.01, 1.01)`;
            card.style.setProperty('--mouse-x', `${(x / rect.width) * 100}%`);
            card.style.setProperty('--mouse-y', `${(y / rect.height) * 100}%`);
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        });
    });
}

/**
 * Ambient 3D Constellation Particle Canvas
 */
function initAmbientCanvas() {
    const canvas = document.getElementById('ambientCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const count = 40;

    for (let i = 0; i < count; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            radius: Math.random() * 2 + 0.8,
            vx: (Math.random() - 0.5) * 0.35,
            vy: (Math.random() - 0.5) * 0.35,
            alpha: Math.random() * 0.45 + 0.2
        });
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(165, 180, 252, ${p.alpha})`;
            ctx.fill();

            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 100) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(99, 102, 241, ${(1 - dist / 100) * 0.12})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    animate();
}

/**
 * Aesthetic Toast Notification
 */
function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✨' : '⚠️';
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px) scale(0.95)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

// Global expose
window.deleteExpense = deleteExpense;


/**
 * ==========================================================================
 * AI FINANCIAL ASSISTANT (RAG) CHATBOT CLIENT
 * ==========================================================================
 */

// AI Controller API Host - Pointing directly to Live Render Cloud Backend
window.AI_API_BASE_URL = 'https://expence2-0.onrender.com';

function initAiAssistant() {
    const openAiChatBtn = document.getElementById('openAiChatBtn');
    const floatingAiBtn = document.getElementById('floatingAiBtn');
    const closeAiChatBtn = document.getElementById('closeAiChatBtn');
    const clearAiChatBtn = document.getElementById('clearAiChatBtn');
    const aiChatDrawer = document.getElementById('aiChatDrawer');
    const aiChatMessages = document.getElementById('aiChatMessages');
    const aiTypingIndicator = document.getElementById('aiTypingIndicator');
    const aiChatForm = document.getElementById('aiChatForm');
    const aiChatInput = document.getElementById('aiChatInput');
    const aiBackendStatus = document.getElementById('aiBackendStatus');

    if (!aiChatDrawer) return;

    // Toggle Chat Drawer
    const toggleAiDrawer = (show) => {
        const isActive = aiChatDrawer.classList.contains('active');
        const nextState = show !== undefined ? show : !isActive;
        if (nextState) {
            aiChatDrawer.classList.add('active');
            if (aiChatInput) aiChatInput.focus();
            checkBackendHealth();
        } else {
            aiChatDrawer.classList.remove('active');
        }
    };

    if (openAiChatBtn) openAiChatBtn.addEventListener('click', () => toggleAiDrawer(true));
    if (floatingAiBtn) floatingAiBtn.addEventListener('click', () => toggleAiDrawer(true));
    if (closeAiChatBtn) closeAiChatBtn.addEventListener('click', () => toggleAiDrawer(false));

    // Clear Chat
    if (clearAiChatBtn) {
        clearAiChatBtn.addEventListener('click', () => {
            if (confirm('Clear chat conversation?')) {
                aiChatMessages.innerHTML = `
                    <div class="ai-message ai-assistant-message">
                        <div class="ai-msg-avatar">✨</div>
                        <div class="ai-msg-bubble">
                            <p>Conversation cleared. How can I help you with your expenses, budget, or salary today?</p>
                        </div>
                    </div>
                `;
                renderDefaultSuggestions();
            }
        });
    }

    // Check Backend Health
    async function checkBackendHealth() {
        try {
            const res = await fetch(`${window.AI_API_BASE_URL}/health`, { method: 'GET' });
            if (res.ok && aiBackendStatus) {
                aiBackendStatus.textContent = 'Hybrid RAG • Connected';
                aiBackendStatus.style.color = '#34d399';
            }
        } catch (e) {
            if (aiBackendStatus) {
                aiBackendStatus.textContent = 'FastAPI Offline (Localhost:8000)';
                aiBackendStatus.style.color = '#f59e0b';
            }
        }
    }

    // Attach listener for suggestion chips
    function bindSuggestionChips() {
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', function() {
                const query = this.getAttribute('data-query') || this.textContent.trim();
                if (aiChatInput) {
                    aiChatInput.value = query;
                    sendUserMessage(query);
                }
            });
        });
    }

    function renderDefaultSuggestions() {
        const existing = document.getElementById('aiQuickSuggestions');
        if (existing) existing.remove();

        const container = document.createElement('div');
        container.className = 'ai-quick-suggestions';
        container.id = 'aiQuickSuggestions';
        container.innerHTML = `
            <span class="suggestion-chip" data-query="Maine is month kitne paise kharch kiye?">💸 Kitna kharch kiya?</span>
            <span class="suggestion-chip" data-query="Where am I spending the most?">📊 Highest expense category?</span>
            <span class="suggestion-chip" data-query="Mera kitna budget remaining hai?">🎯 Budget remaining?</span>
            <span class="suggestion-chip" data-query="How much salary is left?">💼 Salary left?</span>
            <span class="suggestion-chip" data-query="Analyze my 50/30/20 salary rule allocation">⚖️ 50/30/20 breakdown</span>
            <span class="suggestion-chip" data-query="Mujhe paise save karne ke suggestions do.">💡 Savings advice</span>
        `;
        aiChatMessages.appendChild(container);
        bindSuggestionChips();
    }

    bindSuggestionChips();

    // Form Submit
    if (aiChatForm) {
        aiChatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = (aiChatInput.value || '').trim();
            if (!text) return;
            sendUserMessage(text);
        });
    }

    // Send User Message
    async function sendUserMessage(messageText) {
        // Clear input
        if (aiChatInput) aiChatInput.value = '';

        // Append user message bubble
        appendMessage('user', messageText);

        // Hide suggestions
        const existingSug = document.getElementById('aiQuickSuggestions');
        if (existingSug) existingSug.remove();

        // Show typing indicator
        if (aiTypingIndicator) {
            aiTypingIndicator.classList.add('active');
            aiTypingIndicator.style.display = 'block';
        }
        scrollToBottom();

        try {
            // Obtain Firebase ID Token
            let idToken = null;
            if (typeof auth !== 'undefined' && auth.currentUser) {
                try {
                    idToken = await auth.currentUser.getIdToken(true);
                } catch (tokenErr) {
                    console.warn('Could not refresh Firebase token, using fallback:', tokenErr);
                }
            } else if (currentUser && currentUser.uid) {
                idToken = `test-token-${currentUser.uid}`;
            }

            if (!idToken) {
                throw new Error('Authentication required. Please log in again.');
            }

            let response = null;
            // 1. Attempt Vercel Serverless Function /api/chat first
            try {
                const apiRes = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${idToken}`
                    },
                    body: JSON.stringify({
                        message: messageText,
                        month: viewingMonth,
                        year: viewingYear
                    })
                });
                if (apiRes.ok) {
                    response = apiRes;
                }
            } catch (serverlessErr) {
                console.log('/api/chat route not available locally, checking live backend...', serverlessErr);
            }

            // 2. Fallback to Cloud Render backend
            if (!response) {
                response = await fetch(`${window.AI_API_BASE_URL}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${idToken}`
                    },
                    body: JSON.stringify({
                        message: messageText,
                        month: viewingMonth,
                        year: viewingYear
                    })
                });
            }

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `Server responded with status ${response.status}`);
            }

            const data = await response.json();
            
            // Append assistant response
            appendMessage('assistant', data.answer, data.sources);

            // Render suggested follow-ups
            if (data.suggested_followups && data.suggested_followups.length > 0) {
                renderFollowupSuggestions(data.suggested_followups);
            }

        } catch (error) {
            console.error('AI chat error:', error);
            const errorMsg = `⚠️ **Connection Notice:** Could not reach the AI Controller backend (${error.message}).\n\nPlease ensure you are logged in and the AI service is operational.`;
            appendMessage('assistant', errorMsg);
        } finally {
            if (aiTypingIndicator) {
                aiTypingIndicator.classList.remove('active');
                aiTypingIndicator.style.display = 'none';
            }
            scrollToBottom();
        }
    }

    function appendMessage(sender, text, sources = []) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-message ai-${sender}-message`;

        const avatar = document.createElement('div');
        avatar.className = `ai-msg-avatar ${sender === 'user' ? 'ai-user-avatar' : ''}`;
        avatar.textContent = sender === 'user' ? (currentUser ? currentUser.displayName.charAt(0) : 'U') : '✨';

        const bubble = document.createElement('div');
        bubble.className = 'ai-msg-bubble';
        bubble.innerHTML = formatMarkdownText(text);

        // Append collapsible sources if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('details');
            sourcesDiv.className = 'ai-sources-card';
            sourcesDiv.innerHTML = `
                <summary>🔍 ${sources.length} Verified Sources from Firestore</summary>
                <ul style="margin-top: 6px; padding-left: 16px;">
                    ${sources.map(s => `<li>[${s.date}] <strong>${escapeHtml(s.description || '')}</strong>: ₹${s.amount} (${s.category})</li>`).join('')}
                </ul>
            `;
            bubble.appendChild(sourcesDiv);
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        aiChatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    function renderFollowupSuggestions(followups) {
        const existing = document.getElementById('aiQuickSuggestions');
        if (existing) existing.remove();

        const container = document.createElement('div');
        container.className = 'ai-quick-suggestions';
        container.id = 'aiQuickSuggestions';

        followups.forEach(f => {
            const chip = document.createElement('span');
            chip.className = 'suggestion-chip';
            chip.setAttribute('data-query', f);
            chip.textContent = f;
            chip.addEventListener('click', () => {
                if (aiChatInput) aiChatInput.value = f;
                sendUserMessage(f);
            });
            container.appendChild(chip);
        });

        aiChatMessages.appendChild(container);
        scrollToBottom();
    }

    function formatMarkdownText(rawText) {
        if (!rawText) return '';
        let formatted = escapeHtml(rawText);

        // Bold: **text**
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic: *text*
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Bullet points
        formatted = formatted.replace(/(?:^|\n)[•\-\*]\s+(.*)/g, '<br>• $1');
        // Newlines to <br>
        formatted = formatted.replace(/\n\n/g, '<p style="margin-top: 6px;"></p>').replace(/\n/g, '<br>');

        return formatted;
    }

    function scrollToBottom() {
        if (aiChatMessages) {
            aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
        }
    }
}
