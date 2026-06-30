import React, { useState } from 'react';

export const MyComponent = ({ title }: { title: string }) => {
    const [count, setCount] = useState(0);
    
    // Complex business logic
    const handleIncrement = () => {
        setCount(c => c + 1);
    };

    return (
        <div className="container">
            <h1>{title}</h1>
            <button onClick={handleIncrement}>Click {count}</button>
        </div>
    );
};
