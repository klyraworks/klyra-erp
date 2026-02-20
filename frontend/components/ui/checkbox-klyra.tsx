import React from 'react';

interface CheckboxKlyraProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  className?: string;
}

export function CheckboxKlyra({ checked, onChange, label, className = '' }: CheckboxKlyraProps) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`
        relative inline-flex items-center gap-2 px-3 py-2 rounded-lg
        transition-all duration-200 ease-out border
        ${checked 
          ? 'bg-primary text-primary-foreground shadow-sm' 
          : 'bg-muted/50 text-muted-foreground hover:bg-muted'
        }
        ${className}
      `}
    >
      <div className={`
        relative flex items-center justify-center w-5 h-5 rounded
        transition-all duration-200
        ${checked ? 'bg-primary-foreground/20' : 'bg-background/50'}
      `}>
        <svg
          viewBox="0 0 24 24"
          className={`
            w-4 h-4 transition-all duration-200
            ${checked 
              ? 'scale-100 opacity-100' 
              : 'scale-0 opacity-0'
            }
          `}
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
      {label && (
        <span className="text-sm font-medium">
          {label}
        </span>
      )}
    </button>
  );
}