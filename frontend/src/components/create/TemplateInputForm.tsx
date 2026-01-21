import { useState } from 'react';
import { Template, TemplateInputs } from '@/types/template';
import { ChevronLeft } from 'lucide-react';

interface TemplateInputFormProps {
  template: Template;
  values: TemplateInputs;
  onChange: (values: TemplateInputs) => void;
  onBack: () => void;
  onStart: () => void;
}

export function TemplateInputForm({
  template,
  values,
  onChange,
  onBack,
  onStart,
}: TemplateInputFormProps) {
  const [touched, setTouched] = useState<Set<string>>(new Set());

  const allInputs = [...template.requiredInputs, ...template.optionalInputs];
  const requiredInputs = template.requiredInputs;

  const isRequiredValid = requiredInputs.every((input) => {
    const value = values[input.id]?.trim();
    return value && value.length > 0;
  });

  const handleInputChange = (inputId: string, value: string) => {
    onChange({
      ...values,
      [inputId]: value,
    });
  };

  const handleInputBlur = (inputId: string) => {
    setTouched((prev) => new Set(prev).add(inputId));
  };

  const handleStart = () => {
    // Mark all required fields as touched to show errors
    const newTouched = new Set(touched);
    requiredInputs.forEach((input) => newTouched.add(input.id));
    setTouched(newTouched);

    if (isRequiredValid) {
      onStart();
    }
  };

  const renderInput = (input: typeof allInputs[0]) => {
    const value = values[input.id] || '';
    const showError = touched.has(input.id) && input.required && !value.trim();

    return (
      <div key={input.id} className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {input.label}
          {input.required && <span className="text-red-500 ml-1">*</span>}
        </label>

        {input.type === 'textarea' ? (
          <textarea
            value={value}
            onChange={(e) => handleInputChange(input.id, e.target.value)}
            onBlur={() => handleInputBlur(input.id)}
            placeholder={input.placeholder}
            rows={4}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              showError ? 'border-red-300' : 'border-gray-300'
            }`}
          />
        ) : (
          <input
            type={input.type === 'image' ? 'url' : input.type}
            value={value}
            onChange={(e) => handleInputChange(input.id, e.target.value)}
            onBlur={() => handleInputBlur(input.id)}
            placeholder={input.placeholder}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              showError ? 'border-red-300' : 'border-gray-300'
            }`}
          />
        )}

        {showError && (
          <p className="text-sm text-red-500 mt-1">This field is required</p>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-xl mx-auto">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6 transition-colors"
      >
        <ChevronLeft size={20} />
        <span>Back to templates</span>
      </button>

      <div className="text-center mb-8">
        <span className="text-5xl mb-4 block">{template.icon}</span>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Create a {template.name}
        </h1>
        <p className="text-gray-500">{template.description}</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        {requiredInputs.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Required Information
            </h3>
            {requiredInputs.map(renderInput)}
          </div>
        )}

        {template.optionalInputs.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Optional (add these later if you want)
            </h3>
            {template.optionalInputs.map(renderInput)}
          </div>
        )}

        <button
          onClick={handleStart}
          disabled={!isRequiredValid}
          className="w-full mt-6 py-3 px-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          Start Creating
        </button>
      </div>
    </div>
  );
}
