'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface OnboardingFormProps {
    onComplete: (data: UserData) => void;
}

interface UserData {
    name: string;
    age: string;
    concerns: string;
}

const steps = [
    { id: 'name', label: 'What should we call you?', subtitle: 'Choose any name you feel comfortable with' },
    { id: 'age', label: 'How old are you?', subtitle: 'This helps us provide more relevant support' },
    { id: 'concerns', label: 'What brings you here today?', subtitle: 'Feel free to share as much as you\'re comfortable with' },
];

const stepSubtitles: Record<number, string> = {
    0: "Hi there! What's your name?",
    1: "Great to meet you! How old are you?",
    2: "Now, what brings you here today?",
};

export default function OnboardingForm({ onComplete }: OnboardingFormProps) {
    const [currentStep, setCurrentStep] = useState(0);
    const [formData, setFormData] = useState<UserData>({
        name: '',
        age: '',
        concerns: '',
    });
    const [errors, setErrors] = useState<Partial<UserData>>({});

    const validateStep = () => {
        const newErrors: Partial<UserData> = {};

        if (currentStep === 0 && !formData.name.trim()) {
            newErrors.name = 'Please enter your name';
        }
        if (currentStep === 1) {
            if (!formData.age.trim()) {
                newErrors.age = 'Please enter your age';
            } else if (isNaN(Number(formData.age)) || Number(formData.age) < 13 || Number(formData.age) > 120) {
                newErrors.age = 'Please enter a valid age between 13 and 120';
            }
        }
        if (currentStep === 2 && !formData.concerns.trim()) {
            newErrors.concerns = 'Please share your concerns';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validateStep()) {
            if (currentStep < steps.length - 1) {
                setCurrentStep(currentStep + 1);
            } else {
                onComplete(formData);
            }
        }
    };

    const handleBack = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (errors[name as keyof UserData]) {
            setErrors(prev => ({ ...prev, [name]: undefined }));
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleNext();
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md"
            >
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-8 space-y-8">
                    {/* Progress Bar */}
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm text-gray-400">
                            <span className="text-indigo-600">
                                {stepSubtitles[currentStep]}
                            </span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-1.5">
                            <motion.div
                                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-1.5 rounded-full"
                                initial={{ width: 0 }}
                                animate={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                                transition={{ duration: 0.5, ease: "easeOut" }}
                            />
                        </div>
                    </div>

                    {/* Form Content */}
                    <div className="space-y-6">
                        <div className="text-center space-y-2">
                            <h2 className="text-2xl font-medium text-gray-800">
                                {steps[currentStep].label}
                            </h2>
                            <p className="text-gray-500 text-sm">
                                {steps[currentStep].subtitle}
                            </p>
                        </div>

                        <motion.div
                            key={currentStep}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ duration: 0.3 }}
                            className="space-y-2"
                        >
                            {currentStep === 0 && (
                                <input
                                    type="text"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleChange}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Enter your name"
                                    className={`w-full px-4 py-3 border ${errors.name ? 'border-red-300 bg-red-50' : 'border-gray-200'
                                        } rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200`}
                                    autoFocus
                                />
                            )}

                            {currentStep === 1 && (
                                <input
                                    type="number"
                                    name="age"
                                    value={formData.age}
                                    onChange={handleChange}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Enter your age"
                                    className={`w-full px-4 py-3 border ${errors.age ? 'border-red-300 bg-red-50' : 'border-gray-200'
                                        } rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200`}
                                    autoFocus
                                />
                            )}

                            {currentStep === 2 && (
                                <textarea
                                    name="concerns"
                                    value={formData.concerns}
                                    onChange={handleChange}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Share what's on your mind..."
                                    className={`w-full px-4 py-3 border ${errors.concerns ? 'border-red-300 bg-red-50' : 'border-gray-200'
                                        } rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent h-32 transition-all duration-200 resize-none`}
                                    autoFocus
                                />
                            )}

                            {errors[steps[currentStep].id as keyof UserData] && (
                                <motion.p
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-red-500 text-sm"
                                >
                                    {errors[steps[currentStep].id as keyof UserData]}
                                </motion.p>
                            )}
                        </motion.div>
                    </div>

                    {/* Navigation Buttons */}
                    <div className="flex space-x-4">
                        {currentStep > 0 && (
                            <motion.button
                                onClick={handleBack}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                className="flex-1 bg-gray-50 text-gray-700 py-3 px-6 rounded-xl hover:bg-gray-100 transition-all duration-200"
                            >
                                Back
                            </motion.button>
                        )}
                        <motion.button
                            onClick={handleNext}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className={`flex-1 bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-3 px-6 rounded-xl hover:from-indigo-600 hover:to-purple-600 transition-all duration-200 shadow-lg ${currentStep === 0 ? 'w-full' : ''
                                }`}
                        >
                            {currentStep === steps.length - 1 ? 'Start Your Journey' : 'Continue'}
                        </motion.button>
                    </div>
                </div>
            </motion.div>
        </div>
    );
} 