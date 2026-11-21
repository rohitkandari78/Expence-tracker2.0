// Firebase Configuration

const firebaseConfig = {
  apiKey: "AIzaSyDtO8HhSPTS6oBcSzjNIEDD_LhqCugHlR8",
  authDomain: "yourmemo-9dec5.firebaseapp.com",
  databaseURL: "https://yourmemo-9dec5-default-rtdb.firebaseio.com",
  projectId: "yourmemo-9dec5",
  storageBucket: "yourmemo-9dec5.firebasestorage.app",
  messagingSenderId: "1099064122453",
  appId: "1:1099064122453:web:4f2312216838cbd0fc48dc",
  measurementId: "G-GLHGTYGSZD"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize services
const auth = firebase.auth();
const db = firebase.firestore();

// Configure Google Auth Provider
const googleProvider = new firebase.auth.GoogleAuthProvider();

// Export for use in other files
window.auth = auth;
window.db = db;
window.googleProvider = googleProvider;

console.log('Firebase initialized successfully');