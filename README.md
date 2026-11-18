# Smart Expense Tracker 3D - Spatial & Employee Salary Edition
 
A next-generation, aesthetic 3D expense and salary tracking web application designed for salaried employees and working professionals. Features interactive spatial glassmorphism, physical card tilt physics, tactile push controls, automated net savings calculations, and 50/30/20 salary budget analytics.

## 🚀 3D & Aesthetic Highlights

- 💎 **3D Holographic Titanium Card**: Dynamic perspective tilt with interactive mouse-tracking specular reflection, EMV metallic chip design, embossed foil figures, and real-time in-hand salary ribbon.
- 💼 **Employee Salary & Net Savings Engine**: Set monthly in-hand salary, employer/company name, and payday. Automatically calculates **Net In-Pocket Savings** (`Salary - Total Expenses`) and **Savings Rate %**.
- 📊 **50 / 30 / 20 Salary Health Advisor**: Live visual breakdown tracking your paycheck across **Needs** (≤50%: Rent, Bills, Groceries, Fuel), **Wants** (≤30%: Dining, Cinema, Shopping), and **Savings** (≥20%: Retained bank balance).
- 🔄 **Dual Transaction Logging (Expense 🔴 vs Salary/Income 🟢)**: Record debited expenses or credited salary, bonuses, freelance payouts, and investment returns.
- ⚡ **3D Tactile Push Buttons**: Physical mechanical button push physics with depth layers and hover lift.
- 🌌 **3D Ambient Constellation Canvas**: Interactive floating starfield background with subtle connection physics.
- 🔮 **Spatial Glassmorphism**: Frosted multi-layer translucent glass surfaces with specular highlights and glowing neon gradients.
- 🔍 **Instant Search & Type Filter Tabs**: Filter by "All", "🔴 Expenses", or "🟢 Salary & Income", plus live keyword search.
- 🤝 **Dual-Mode Persistence**: Works out of the box with Firebase Cloud Firestore or instantaneous LocalStorage Guest Demo mode.

## 📁 Project Structure

```
expense-tracker/
│
├── index.html                 # Entry redirect
│
├── login/                     # 3D Spatial Login Module
│   ├── login.html            # Holographic login screen
│   ├── login.css             # 3D spatial glassmorphism styles
│   └── login.js              # Auth & ambient particle engine
│
├── dashboard/                 # 3D Dashboard Module
│   ├── dashboard.html        # Main 3D dashboard (with Employee & Salary UI)
│   ├── dashboard.css         # Spatial dark-mode luxury theme & 3D cards
│   └── dashboard.js          # Controller, 3D tilt engine & salary calculations
│
├── js/                        # Core Shared Scripts
│   ├── firebase-config.js    # Firebase initialization
│   └── classes.js            # OOP Models (User, Expense, Manager with Salary methods)
│
└── README.md                  # Project documentation
```

## ✨ Core Features for Salaried Employees

- ✅ **Employee Salary Profile** - Set in-hand salary, company/organization name, and monthly payday
- ✅ **Net Savings & Savings Rate** - Instant visibility into how much of your salary is actually saved each month
- ✅ **50/30/20 Rule Advisor** - Benchmark your lifestyle to ensure you never overspend on wants or under-save
- ✅ **Income & Salary Credit Logging** - Log salary credits with green glowing badges and distinct category icons
- ✅ **3D Titanium Budget Card** - Set and monitor monthly budgets with realistic 3D depth
- ✅ **Smart Bill Splitting** - Calculate shares among friends/colleagues with live cost preview
- ✅ **Dual Auth (Google & Guest Demo)** - Zero friction test mode or cloud syncing
- ✅ **Fully Responsive 3D Experience** - Fluid layout adapting to mobile, tablet, and desktop

---
