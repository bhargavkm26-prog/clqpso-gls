import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, ArrowRight } from 'lucide-react';

interface StatusPopupProps {
  logs: string[];
  isComplete: boolean;
}

export default function StatusPopup({ logs, isComplete }: StatusPopupProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (logs.length > 0 && !isComplete) {
      setIsVisible(true);
    } else if (isComplete) {
      // Fade out after a short delay when complete
      const t = setTimeout(() => setIsVisible(false), 2000);
      return () => clearTimeout(t);
    }
  }, [logs.length, isComplete]);

  if (!isVisible && logs.length === 0) return null;

  return (
    <div 
      className={`absolute bottom-8 right-8 w-[350px] bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-2xl z-[500] transition-all duration-500 transform ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-[150%] opacity-0'
      }`}
    >
      <div className="flex items-center mb-3">
        {isComplete ? (
          <CheckCircle2 className="w-5 h-5 text-emerald-500 mr-3 shrink-0" />
        ) : (
          <Loader2 className="w-5 h-5 text-blue-500 animate-spin mr-3 shrink-0" />
        )}
        <h3 className="text-sm font-semibold text-slate-50">
          {isComplete ? 'Optimization Running' : 'Orchestrating Backend...'}
        </h3>
      </div>
      
      <div className="flex flex-col gap-2 text-xs">
        {logs.map((log, index) => {
          const isLast = index === logs.length - 1;
          const isDone = !isLast || isComplete;
          
          return (
            <div 
              key={index} 
              className={`flex items-start transition-all duration-300 ${
                isDone ? 'text-emerald-500' : 'text-slate-400'
              }`}
            >
              <span className="mr-2 mt-[2px] shrink-0">
                {isDone ? <CheckCircle2 className="w-3 h-3" /> : <ArrowRight className="w-3 h-3" />}
              </span>
              <span>{log}{isDone ? ' (Done)' : '...'}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
