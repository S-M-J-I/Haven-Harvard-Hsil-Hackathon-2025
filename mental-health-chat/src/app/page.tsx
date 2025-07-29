'use client';

import { useState } from 'react';
import OnboardingForm from '@/components/OnboardingForm';
import ChatInterface from '@/components/ChatInterface';

interface UserData {
    name: string;
    age: string;
    concerns: string;
}

export default function Home() {
    const [userData, setUserData] = useState<UserData | null>(null);

    const handleOnboardingComplete = (data: UserData) => {
        setUserData(data);
    };

    return (
        <main className="min-h-screen">
            {!userData ? (
                <OnboardingForm onComplete={handleOnboardingComplete} />
            ) : (
                <ChatInterface userName={userData.name} />
            )}
        </main>
    );
} 