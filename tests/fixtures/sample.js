function calculateMetrics(data) {
    // Calculates important business metrics.
    const values = Object.values(data);
    const total = values.reduce((a, b) => a + b, 0);
    return total / 100.0;
}

class Processor {
    constructor() {
        this.ready = true;
    }
    
    async processAsync(item) {
        // async processing
        const res = await fetch(item);
        return res.json();
    }
}

const helper = (a, b) => {
    return a + b;
};
