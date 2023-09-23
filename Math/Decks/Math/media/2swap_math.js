function fermatlittletheorem(a) {
    const p = 3;

    var htmlResult = a+`<sup>`+p+`</sup> ≡ `+(a**p)+` ≡ `+a+` (mod `+p+`)`;

    return htmlResult;
}

function factorial(n) {
  if (n < 1) {
    return 'Factorial is not defined for n < 1';
  }

  let htmlResult = '';
  let factorial = 1;

  for (let i = 1; i <= n; i++) {
    factorial *= i;

    htmlResult += `<br>${factorial}`;

    let lineResult = '';
    for (let j = i+1; j <= n; j++) {
      if (j !== i) {
        lineResult += '*';
      }
      lineResult += j;
    }

    htmlResult += lineResult;
  }

  return htmlResult;
}

function geommean(numbers) {
  if (numbers.length === 0) {
    return 'Geometric mean is undefined for an empty array.';
  }

  let product = 1;

  for (let i = 0; i < numbers.length; i++) {
    if (numbers[i] <= 0) {
      return 'Geometric mean is undefined for non-positive numbers.';
    }
    product *= numbers[i];
  }

  const geometricMean = Math.pow(product, 1 / numbers.length);

  const htmlResult = '(' + numbers.join('*') + ')<sup>1/' + numbers.length + '</sup> = ' + product + '<sup>1/' + numbers.length + '</sup> = ' + geometricMean.toFixed(10);

  return htmlResult;
}

function primenumbertheorem(N) {
  const piNApproximation = N / Math.log(N);

  const htmlResult = `pi(${N}) ≈ ${N} / ln(${N}) ≈ ${piNApproximation.toFixed(10)}`;

  return htmlResult;
}

function wilson(n) {
  if (n <= 1) {
    return '0 and 1 are not prime numbers.';
  }

  // Calculate (n - 1)!
  let factorial = 1;
  let factorialString = '1';
  for (let i = 2; i < n; i++) {
    factorial = (factorial * i) % n;
    factorialString += `*${i}`;
  }

  // Check if (n - 1)! + 1 is divisible by n
  if ((factorial + 1) % n === 0) {
    return `By Wilson's Theorem:<br>(${n} - 1)! + 1 = ${factorialString} + 1 = ${factorial + 1}<br>is divisible by ${n}, so ${n} is a prime number.`;
  } else {
    return `By Wilson's Theorem:<br>(${n} - 1)! + 1 = ${factorialString} + 1 = ${factorial + 1}<br>is not divisible by ${n}, so ${n} is not a prime number.`;
  }
}