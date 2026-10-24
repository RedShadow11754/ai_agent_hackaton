import { Link } from "react-router-dom";

interface StepperProps {
  currentStep: number; // 1-4
}

export function Stepper({ currentStep }: StepperProps) {
  const steps = [
    { number: 1, label: 'Investigate' },
    { number: 2, label: 'Results' },
    { number: 3, label: 'Review' },
    { number: 4, label: 'Saved' },
  ];
  
  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => (
        <div key={step.number} className="flex items-center flex-1">
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step.number === currentStep
                  ? 'bg-indigo-600 text-white'
                  : step.number < currentStep
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-slate-200 text-slate-600'
              }`}
            >
              {step.number}
            </div>
             <Link to={step.link}>
              <span
                className={`text-sm font-medium ${step.number === currentStep
                    ? 'text-indigo-700'
                    : step.number < currentStep
                      ? 'text-indigo-600'
                      : 'text-slate-600'
                  }`}
              >
                {step.label}
              </span>
            </Link>
          </div>
          {index < steps.length - 1 && (
            <div
              className={`flex-1 h-px mx-4 ${
                step.number < currentStep ? 'bg-indigo-300' : 'bg-slate-300'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}
