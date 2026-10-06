const assert = require('node:assert/strict');
const model = require('./learning-model.cjs');
const data = model.dataset();
const weights = model.initial();
const analytic = model.gradient(weights, data);
let maxGradientError = 0;
for (let i = 0; i < weights.length; i++) {
  const h = 1e-5, plus = weights.slice(), minus = weights.slice();
  plus[i] += h; minus[i] -= h;
  const numeric = (model.loss(plus, data) - model.loss(minus, data)) / (2 * h);
  maxGradientError = Math.max(maxGradientError, Math.abs(numeric - analytic[i]));
}
assert.ok(maxGradientError < 1e-7, 'Backpropagation must match finite differences');
const { frames } = model.timeline();
const first = frames[0], last = frames.at(-1);
const accuracy = w => data.filter(d => (model.forward(w, d.x, d.y).probability >= .5 ? 1 : 0) === d.label).length / data.length;
assert.ok(last.loss < first.loss * .1, 'Training must substantially reduce cross-entropy');
assert.equal(accuracy(last.w), 1, 'The final frame must classify the toy training set correctly');
assert.ok(frames.every(frame => frame.w.every(Number.isFinite)), 'All snapshots must be finite');
console.log(JSON.stringify({ maxGradientError, initialLoss: first.loss, finalLoss: last.loss, initialTrainingAccuracy: accuracy(first.w), finalTrainingAccuracy: accuracy(last.w), snapshots: frames.length }, null, 2));
