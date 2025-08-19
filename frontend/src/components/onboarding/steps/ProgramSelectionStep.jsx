/**
 * ProgramSelectionStep Component
 * 
 * Helps students choose their academic program and specialization.
 */

import React, { useState } from 'react';
import { GraduationCap, CheckCircle } from 'lucide-react';

const ProgramSelectionStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [selectedProgram, setSelectedProgram] = useState(studentData.primary_major || '');

  const programs = [
    { id: 'cs', name: 'Computer Science', description: 'Software development, algorithms, and computing systems' },
    { id: 'business', name: 'Business Administration', description: 'Management, finance, and business strategy' },
    { id: 'engineering', name: 'Engineering', description: 'Design and build technology solutions' },
    { id: 'healthcare', name: 'Healthcare', description: 'Medical and health-related programs' },
    { id: 'education', name: 'Education', description: 'Teaching and educational leadership' },
  ];

  const handleProgramSelect = async (program) => {
    setSelectedProgram(program.name);
    const updatedData = { ...studentData, primary_major: program.name };
    onUpdateData(updatedData);
    await onSaveProgress(updatedData);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Select Your Program</h3>
          <p className="text-gray-600">
            Choose the academic program that best aligns with your interests and career goals.
          </p>
        </div>

        <div className="space-y-3">
          {programs.map((program) => (
            <div
              key={program.id}
              className={`p-4 border rounded-lg cursor-pointer transition-all ${
                selectedProgram === program.name
                  ? 'border-red-500 bg-red-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => handleProgramSelect(program)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{program.name}</h4>
                  <p className="text-sm text-gray-600">{program.description}</p>
                </div>
                {selectedProgram === program.name && (
                  <CheckCircle className="w-6 h-6 text-red-600" />
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <GraduationCap className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-blue-900 mb-1">
                Program Selection
              </h4>
              <p className="text-sm text-blue-700">
                Don't worry if you're unsure - you can change your program later. 
                This helps us provide relevant course recommendations.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgramSelectionStep;