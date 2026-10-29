import { parse } from 'acorn';
import { readFileSync, readdirSync } from 'node:fs';
for (const name of readdirSync('app', { recursive: true }).filter(f => f.endsWith('.js'))) {
  parse(readFileSync('app/' + name, 'utf8'), { ecmaVersion: 5 });
}
console.log('All packaged JavaScript parses as ES5.');
