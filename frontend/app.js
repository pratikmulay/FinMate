const screens = {
  quiz: document.getElementById('screen-quiz'),
  loading: document.getElementById('screen-loading'),
  error: document.getElementById('screen-error'),
  dashboard: document.getElementById('screen-dashboard'),
};

function showScreen(name) {
  Object.values(screens).forEach(s => s.classList.add('hidden'));
  screens[name].classList.remove('hidden');
}

let allocChart = null;
let projChart = null;

document.getElementById('quiz-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  document.getElementById('err-savings').style.display = 'none';

  const monthly_income = Number(document.getElementById('monthly_income').value);
  const monthly_savings = Number(document.getElementById('monthly_savings').value);

  if (monthly_savings > monthly_income) {
    document.getElementById('err-savings').style.display = 'block';
    return;
  }

  const payload = {
    monthly_income,
    monthly_savings,
    quiz: {
      age: Number(document.getElementById('age').value),
      horizon: document.getElementById('horizon').value,
      drop_reaction: document.getElementById('drop_reaction').value,
      income_stability: document.getElementById('income_stability').value,
      experience: document.getElementById('experience').value,
      emergency_months: Number(document.getElementById('emergency_months').value),
    },
  };

  showScreen('loading');

  try {
    const res = await fetch('/api/v1/portfolio/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.status === 422) {
      const body = await res.json();
      const msg = body.detail?.[0]?.msg || 'Please check your inputs.';
      throw new Error(msg);
    }
    if (!res.ok) throw new Error(`Server error (${res.status})`);

    const data = await res.json();
    renderDashboard(data);
    showScreen('dashboard');
  } catch (err) {
    document.getElementById('error-message').textContent = err.message || 'Could not reach the server.';
    showScreen('error');
  }
});

document.getElementById('error-retry').addEventListener('click', () => showScreen('quiz'));
document.getElementById('dash-retake').addEventListener('click', () => {
  document.getElementById('quiz-form').reset();
  showScreen('quiz');
});

function renderDashboard(data) {
  document.getElementById('dash-score').textContent = Math.round(data.risk.score);
  document.getElementById('dash-profile').textContent = data.risk.profile;

  const chip = document.getElementById('dash-source');
  chip.textContent = data.source;
  chip.className = `chip ${data.source}`;

  const reasons = document.getElementById('dash-reasons');
  reasons.innerHTML = '';
  (data.risk.reasons || []).forEach(r => {
    const li = document.createElement('li');
    li.textContent = r;
    reasons.appendChild(li);
  });

  const insights = document.getElementById('dash-insights');
  insights.innerHTML = '';
  (data.insights || []).forEach(i => {
    const li = document.createElement('li');
    li.textContent = i;
    insights.appendChild(li);
  });
  if (!data.insights || data.insights.length === 0) {
    insights.innerHTML = '<li>No flags — your profile looks balanced.</li>';
  }

  const tbody = document.querySelector('#dash-table tbody');
  tbody.innerHTML = '';
  data.allocations.forEach(a => {
   const tr = document.createElement('tr');
tr.title = a.rationale;
tr.innerHTML = `
  <td>${a.name}</td>
  <td>${a.asset_class}</td>
  <td>${a.weight_pct.toFixed(1)}%</td>
  <td>₹${Math.round(a.monthly_amount).toLocaleString('en-IN')}</td>
`;
tbody.appendChild(tr);
  });

  document.getElementById('dash-summary').textContent = data.summary;
  document.getElementById('dash-disclaimer').textContent = data.disclaimer;

  renderAllocChart(data.allocations);
  renderProjChart(data.projections);
}

function renderAllocChart(allocations) {
  const ctx = document.getElementById('chart-allocation');
  if (allocChart) allocChart.destroy();
  allocChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: allocations.map(a => a.name),
      datasets: [{
        data: allocations.map(a => a.weight_pct),
        backgroundColor: ['#A9812F', '#5C6F5E', '#A64B2A', '#1B2420', '#C9B679', '#8AA091', '#D68A6E'],
        borderColor: '#FAF7F0',
        borderWidth: 2,
      }],
    },
    options: {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom', labels: { font: { family: 'IBM Plex Sans' } } } },
},
  });
}

function renderProjChart(projections) {
  const ctx = document.getElementById('chart-projection');
  if (projChart) projChart.destroy();
  projChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: projections.map(p => `Yr ${p.years}`),
      datasets: [
        { label: 'Invested', data: projections.map(p => p.invested), borderColor: '#1B2420', borderDash: [4, 4], fill: false },
        { label: 'Pessimistic', data: projections.map(p => p.pessimistic), borderColor: '#A64B2A', fill: false },
        { label: 'Expected', data: projections.map(p => p.expected), borderColor: '#A9812F', borderWidth: 2, fill: false },
        { label: 'Optimistic', data: projections.map(p => p.optimistic), borderColor: '#5C6F5E', fill: false },
      ],
    },
    options: {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom', labels: { font: { family: 'IBM Plex Sans' } } } },
  scales: { y: { ticks: { callback: v => '₹' + v.toLocaleString('en-IN') } } },
},
  });
}