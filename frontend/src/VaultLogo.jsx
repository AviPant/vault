import React from 'react';

export default function VaultLogo({ className = "", size = 24 }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      {/* Cybernetic Shield Base */}
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" strokeWidth="2.2" />
      
      {/* V.A.U.L.T. internal node structure */}
      <path d="M8.5 9.5L12 13.5L15.5 9.5" strokeWidth="2" />
      <path d="M12 13.5V17.5" strokeWidth="2" />
      
      {/* Data point dot */}
      <circle cx="12" cy="6.5" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  );
}
