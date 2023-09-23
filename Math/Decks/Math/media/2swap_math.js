function fermatsLittleTheorem(a) {
    // Calculate p and exponent
    const p = 3;
    const exponent = p - 1;

    // Step 1: Calculate a^(p-1)
    const apMinus1 = Math.pow(a, exponent);

    // Step 2: Calculate a^(p-1) mod p
    const apMinus1ModP = apMinus1 % p;

    // Output the steps
    const result = `
        Step 1: ${a}^(${exponent}) = ${a}^${exponent} = ${apMinus1}
        Step 2: ${apMinus1} mod ${p} = ${apMinus1ModP}
    `;

    return result;
}

function factorial(n) {
    // Initialize the result
    let result = 1;
    let stepsHTML = `<p>Factorial of ${n}:</p><ol>`;

    // Iterate from 1 to n and multiply each number
    for (let i = 1; i <= n; i++) {
        result *= i;
        stepsHTML += `<li>Multiplying by ${i}: ${result}</li>`;
    }

    stepsHTML += `</ol>`;
    
    // Return the result and steps as an HTML string
    return stepsHTML;
}