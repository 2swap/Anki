function fermatlittletheorem(a) {
    const p = 3;

    var htmlResult = a+`<sup>`+p+`</sup> ≡ `+(a**p)+` ≡ `+a+` (mod `+p+`)`;

    return htmlResult;
}

/* EXAMPLE
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
}*/

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

function isPrime(num) {
  if (num <= 1) return false;
  for (let i = 2, sqrt = Math.sqrt(num); i <= sqrt; i++) {
    if (num % i === 0) return false;
  }
  return true;
}

function totient(n) {
  if (n === 1) return 1;
  let result = n;
  if (n % 2 === 0) {
    while (n % 2 === 0) n /= 2;
    result -= result / 2;
  }
  for (let i = 3; i <= Math.sqrt(n); i += 2) {
    if (n % i === 0) {
      while (n % i === 0) n /= i;
      result -= result / i;
    }
  }
  if (n > 1) result -= result / n;
  return result;
}

function mobius(n) {
  if (n === 1) return 1;
  let result = 1;
  let p = 0;
  for (let i = 2; i * i <= n; i++) {
    if (n % i === 0) {
      if (n % (i * i) === 0) return 0; 
      n /= i;
      p++; 
    }
  }
  if (n > 1) p++;
  return (p & 1) ? -1 : 1; 
}

function goldbach(n) {
  if(n==3) return "neither the strong nor weak conjecture makes a claim about n=3."
  if(n % 2 === 0){
    for (let i = 2; i < n; i++) {
      if (isPrime(i) && isPrime(n - i)) {
        return `Goldbach Strong: ${n} = ${i} + ${n - i}`;
      }
    }
  } else {
    for (let i = 2; i < n; i++) {
      for (let j = i; j < n; j++) {
        if (isPrime(i) && isPrime(j) && isPrime(n - i - j)) {
          return `Goldbach Weak: ${n} = ${i} + ${j} + ${n - i - j}`;
        }
      }
    }
  }
  return '';
}

function zeta(n) {
  let realPart = 1 + 1/Math.pow(2, n) + 1/Math.pow(3, n) + 1/Math.pow(4, n);
  return `${realPart.toFixed(4)} + 0i`;
}

function variance(l) {
  const mean = l.reduce((acc, x) => acc + x, 0) / l.length;
  return l.reduce((acc, x) => acc + Math.pow(x - mean, 2), 0) / l.length;
}

function standard_deviation(l) {
  return Math.sqrt(variance(l));
}

function factorial(n) {
    return (n === 0 || n === 1) ? 1 : n * factorial(n - 1);
}

function isPrime(num) {
    if (num <= 1) return false;
    for (let i = 2, sqrt = Math.sqrt(num); i <= sqrt; i++) {
        if (num % i === 0) return false;
    }
    return true;
}

function catalan(n) {
    return factorial(2 * n) / (factorial(n + 1) * factorial(n));
}

function mangoldt(n) {
  if (n <= 1) return 0;
  for (let p = 2; p <= n; p++) {
    if (isPrime(p) && n % p === 0) {
      let k = Math.round(Math.log(n) / Math.log(p));
      if (Math.pow(p, k) === n) {
        return Math.log(p);
      }
    }
  }
  return 0;
}

function bertrand(n) {
    for (let i = n + 1; i < 2 * n; i++) {
        if (isPrime(i)) {
            return i;
        }
    }
    return null; // Just in case, though it shouldn't occur based on Bertrand's postulate.
}

function euclid_gcd(n, m) {
    if (m === 0) return n;
    return euclid_gcd(m, n % m);
}

function mersenne_number(n) {
    let mersenne = Math.pow(2, n) - 1;
    if (isPrime(mersenne)) {
        return `Mersenne number M${n} is ${mersenne} and it is prime.`;
    } else {
        return `Mersenne number M${n} is ${mersenne} and it is not prime.`;
    }
}

function fermat_number(n) {
    let fermat = Math.pow(2, Math.pow(2, n)) + 1;
    if (isPrime(fermat)) {
        return `Fermat number F${n} is ${fermat} and it is prime.`;
    } else {
        return `Fermat number F${n} is ${fermat} and it is not prime.`;
    }
}

