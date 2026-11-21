// ==========================================================================
// 3D SPATIAL LOGIN LOGIC & AMBIENT ENGINE
// ==========================================================================

const googleSignInBtn = document.getElementById('googleSignIn');
const loginCard = document.getElementById('loginCard');

document.addEventListener('DOMContentLoaded', () => {
    // Clear any leftover guest mode session flag
    localStorage.removeItem('expense_tracker_guest_mode');
    initializeAuth();
    setupEventListeners();
    init3DTilt();
    initAmbientCanvas();
});

/**
 * Initialize Firebase Auth State Observer
 */
function initializeAuth() {
    if (typeof auth !== 'undefined' && auth.setPersistence) {
        auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL)
            .catch((error) => console.warn('Persistence error:', error));

        auth.onAuthStateChanged((user) => {
            if (user) {
                console.log('Firebase user active, redirecting to dashboard...');
                window.location.replace('../dashboard/');
            }
        });
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    if (googleSignInBtn) {
        googleSignInBtn.addEventListener('click', signInWithGoogle);
    }
}

/**
 * Sign in with Google (Firebase)
 */
async function signInWithGoogle() {
    try {
        googleSignInBtn.disabled = true;
        const topEl = googleSignInBtn.querySelector('.btn-3d-top');
        if (topEl) {
            topEl.innerHTML = '<span class="loading"></span> Authenticating...';
        }
        
        // Clear any previous guest mode flag
        localStorage.removeItem('expense_tracker_guest_mode');

        const result = await auth.signInWithPopup(googleProvider);
        const user = result.user;
        
        await createUserDocument(user);
        window.location.replace('../dashboard/');
        
    } catch (error) {
        console.error('Sign in error:', error);
        
        let errorMessage = 'Sign in failed. Check your Firebase credentials.';
        if (error.code === 'auth/popup-closed-by-user') {
            errorMessage = 'Sign in was cancelled.';
        } else if (error.code === 'auth/network-request-failed') {
            errorMessage = 'Network error. Please check your connection.';
        } else if (error.code === 'auth/api-key-not-valid' || error.code === 'auth/invalid-api-key') {
            errorMessage = 'Firebase API configuration error. Please verify project settings.';
        }
        
        showToast(errorMessage, 'error');
        
        googleSignInBtn.disabled = false;
        const topEl = googleSignInBtn.querySelector('.btn-3d-top');
        if (topEl) {
            topEl.innerHTML = `
                <svg class="google-icon" width="20" height="20" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.66v3.05h3.87c2.26-2.09 3.67-5.17 3.67-9.15z"/>
                    <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.87-3.05c-1.08.72-2.45 1.16-4.06 1.16-3.13 0-5.78-2.11-6.73-4.96H1.27v3.15C3.25 21.31 7.34 24 12 24z"/>
                    <path fill="#FBBC05" d="M5.27 14.24c-.25-.72-.38-1.49-.38-2.24s.13-1.52.38-2.24V6.61H1.27C.46 8.23 0 10.06 0 12s.46 3.77 1.27 5.39l4-3.15z"/>
                    <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.25 2.69 1.27 6.61l4 3.15c.95-2.85 3.6-4.96 6.73-4.96z"/>
                </svg>
                <span>Continue with Google</span>
            `;
        }
    }
}

/**
 * Create or update user in Firestore
 */
async function createUserDocument(user) {
    try {
        if (!db) return;
        const userRef = db.collection('users').doc(user.uid);
        const userDoc = await userRef.get();
        
        if (!userDoc.exists) {
            await userRef.set({
                uid: user.uid,
                email: user.email,
                displayName: user.displayName,
                photoURL: user.photoURL,
                budgets: {},
                salaries: {},
                employer: '',
                createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            });
        } else {
            await userRef.update({
                updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            });
        }
    } catch (error) {
        console.warn('Firestore user update skipped or failed:', error);
    }
}

/**
 * 3D Physics Card Tilt with Specular Mouse Tracking
 */
function init3DTilt() {
    if (!loginCard) return;

    loginCard.addEventListener('mousemove', (e) => {
        const rect = loginCard.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const maxTilt = 10;
        const rotateX = ((y - centerY) / centerY) * -maxTilt;
        const rotateY = ((x - centerX) / centerX) * maxTilt;

        loginCard.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.02, 1.02, 1.02)`;
        loginCard.style.setProperty('--mouse-x', `${(x / rect.width) * 100}%`);
        loginCard.style.setProperty('--mouse-y', `${(y / rect.height) * 100}%`);
    });

    loginCard.addEventListener('mouseleave', () => {
        loginCard.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    });
}

/**
 * Ambient 3D Particle Starfield Canvas
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
    const count = 45;

    for (let i = 0; i < count; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            radius: Math.random() * 2 + 0.8,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            alpha: Math.random() * 0.5 + 0.2
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

            // Draw faint 3D constellation lines between nearby particles
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 110) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(99, 102, 241, ${(1 - dist / 110) * 0.15})`;
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