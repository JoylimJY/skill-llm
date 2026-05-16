import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "src/components",
    "src/components/forms",
    "src/components/modals",
    "src/components/tables",
    "src/pages",
    "src/utils",
    "src/styles",
    "public/assets/icons",
    "tests/unit",
    "tests/e2e",
    "config",
    "scripts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files (valid / unrelated) ────────────────────────────────────
distractor_files = {
    "config/webpack.config.js": """\
module.exports = {
  entry: './src/index.js',
  output: { path: __dirname + '/dist', filename: 'bundle.js' },
  module: { rules: [{ test: /\\.jsx?$/, use: 'babel-loader' }] }
};
""",
    "config/jest.config.js": """\
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterFramework: ['@testing-library/jest-dom/extend-expect'],
};
""",
    "src/utils/dateFormatter.js": """\
export const formatDate = (date) => new Intl.DateTimeFormat('en-US').format(date);
export const parseISO = (str) => new Date(str);
""",
    "src/utils/httpClient.js": """\
export async function get(url) {
  const res = await fetch(url);
  return res.json();
}
export async function post(url, body) {
  const res = await fetch(url, { method: 'POST', body: JSON.stringify(body) });
  return res.json();
}
""",
    "src/styles/variables.css": """\
:root {
  --color-primary: #0056b3;
  --color-bg: #ffffff;
  --color-text: #333333;
  --font-size-base: 16px;
}
""",
    "src/styles/global.css": """\
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; margin: 0; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
""",
    "scripts/build.sh": """\
#!/bin/bash
npm run build
echo "Build complete"
""",
    "scripts/deploy.sh": """\
#!/bin/bash
echo "Deploying to production..."
rsync -avz dist/ user@server:/var/www/html/
""",
    "tests/unit/dateFormatter.test.js": """\
import { formatDate } from '../../src/utils/dateFormatter';
test('formats date correctly', () => {
  expect(formatDate(new Date('2024-01-15'))).toBe('1/15/2024');
});
""",
    "tests/e2e/login.spec.js": """\
describe('Login flow', () => {
  it('should redirect to dashboard after login', () => {
    cy.visit('/login');
    cy.get('#username').type('patient@example.com');
    cy.get('#password').type('secret');
    cy.get('[data-testid=submit]').click();
    cy.url().should('include', '/dashboard');
  });
});
""",
}

for path, content in distractor_files.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ── PROBLEM FILES: Components with deliberate accessibility violations ────────

# 1. Patient registration form — missing labels, no fieldset/legend, bad placeholder-only pattern
patient_form_html = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Patient Registration</title>
  <link rel="stylesheet" href="../styles/global.css">
</head>
<body>
  <div class="page-wrapper">
    <h1>Patient Portal</h1>
    <div class="registration-section">
      <h3>Create Your Account</h3>
      <!-- VIOLATION: skipped h2, jumped from h1 to h3 -->

      <form id="registration-form" action="/register" method="POST">
        <!-- VIOLATION: input has no associated <label>; placeholder used as label substitute -->
        <input type="text" id="first-name" placeholder="First Name" required>

        <!-- VIOLATION: input has no associated <label> -->
        <input type="text" id="last-name" placeholder="Last Name" required>

        <!-- VIOLATION: email input — label element exists but is NOT associated (missing for/id linkage) -->
        <label>Email Address</label>
        <input type="email" id="email-address" placeholder="you@example.com" required>

        <!-- VIOLATION: password with no label at all -->
        <input type="password" id="pwd" placeholder="Password" required>

        <!-- VIOLATION: checkbox group with no grouping landmark -->
        <input type="checkbox" id="terms"> I agree to terms
        <!-- no <label> wrapping or for attribute on the above -->

        <!-- VIOLATION: submit button uses a div instead of <button> -->
        <div id="submit-btn" onclick="submitForm()">Register</div>
      </form>
    </div>

    <!-- VIOLATION: decorative image used as content image with empty alt AND loaded from <img> -->
    <img src="../assets/icons/doctor.png" alt="">
    <!-- this image conveys meaning ("Our care team") but has empty alt -->

    <!-- VIOLATION: icon-only button with no accessible name -->
    <button id="help-btn">
      <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
      </svg>
    </button>
  </div>
  <script src="../utils/httpClient.js"></script>
</body>
</html>
"""

# 2. Appointment modal dialog — no focus trap, no Esc handler, no role/aria-modal
appointment_modal_js = """\
// AppointmentModal.js
// Renders a modal dialog for booking appointments

export function createAppointmentModal(appointmentData) {
  const overlay = document.createElement('div');
  // VIOLATION: no role="dialog", no aria-modal="true", no aria-labelledby
  overlay.className = 'modal-overlay';
  overlay.id = 'appointment-modal';

  const modal = document.createElement('div');
  modal.className = 'modal-content';
  // VIOLATION: no focus trap implemented — Tab can leave modal freely

  const title = document.createElement('h2');
  title.textContent = 'Book Appointment';
  title.id = 'modal-title';
  // Note: aria-labelledby never wired to this id on the overlay

  // VIOLATION: close button has no accessible name — only an "X" text node
  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'X';
  closeBtn.className = 'modal-close';
  closeBtn.onclick = () => overlay.remove();
  // VIOLATION: Esc key handler not implemented

  const dateLabel = document.createElement('label');
  dateLabel.textContent = 'Appointment Date';
  // VIOLATION: label not associated with input (missing htmlFor / id pair)
  const dateInput = document.createElement('input');
  dateInput.type = 'date';
  dateInput.className = 'date-picker';
  // id missing so label cannot reference it

  const doctorSelect = document.createElement('select');
  // VIOLATION: select has no label
  appointmentData.doctors.forEach(doc => {
    const opt = document.createElement('option');
    opt.value = doc.id;
    opt.textContent = doc.name;
    doctorSelect.appendChild(opt);
  });

  // VIOLATION: confirm button is <a> tag used as button — no role="button", no keyboard activation
  const confirmLink = document.createElement('a');
  confirmLink.href = '#';
  confirmLink.textContent = 'Confirm Booking';
  confirmLink.className = 'confirm-btn';
  confirmLink.onclick = (e) => { e.preventDefault(); bookAppointment(); };

  // VIOLATION: loading state announced nowhere (no aria-live region)
  const loadingDiv = document.createElement('div');
  loadingDiv.id = 'booking-status';
  loadingDiv.textContent = '';
  // no aria-live attribute

  modal.appendChild(title);
  modal.appendChild(closeBtn);
  modal.appendChild(dateLabel);
  modal.appendChild(dateInput);
  modal.appendChild(doctorSelect);
  modal.appendChild(confirmLink);
  modal.appendChild(loadingDiv);
  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // VIOLATION: focus not moved into modal on open
  // overlay.querySelector('[autofocus]') — never called
}

async function bookAppointment() {
  const status = document.getElementById('booking-status');
  status.textContent = 'Booking...';
  // no aria-live, screen reader won't announce
  try {
    await post('/api/appointments', {});
    status.textContent = 'Appointment confirmed!';
  } catch (e) {
    status.textContent = 'Error: could not book appointment.';
    // VIOLATION: error state not announced accessibly
  }
}
"""

# 3. Medical records table — no th scope, no caption, no summary
records_table_html = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Medical Records</title>
</head>
<body>

  <!-- VIOLATION: page has no main landmark -->
  <div class="records-container">
    <h2>Medical Records</h2>

    <!-- VIOLATION: table has no <caption> and no scope on <th> elements -->
    <table id="records-table">
      <thead>
        <tr>
          <!-- VIOLATION: th elements missing scope="col" -->
          <th>Date</th>
          <th>Doctor</th>
          <th>Diagnosis</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>2024-03-15</td>
          <td>Dr. Smith</td>
          <td>Hypertension follow-up</td>
          <td>
            <!-- VIOLATION: icon-only links with no accessible name -->
            <a href="/records/1/view">
              <img src="../assets/icons/eye.png" alt="">
            </a>
            <a href="/records/1/download">
              <img src="../assets/icons/download.png" alt="">
            </a>
          </td>
        </tr>
        <tr>
          <td>2024-02-10</td>
          <td>Dr. Johnson</td>
          <td>Annual physical</td>
          <td>
            <a href="/records/2/view">
              <img src="../assets/icons/eye.png" alt="">
            </a>
            <a href="/records/2/download">
              <img src="../assets/icons/download.png" alt="">
            </a>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- VIOLATION: pagination uses divs instead of nav + button/a -->
    <div class="pagination">
      <div class="page-btn" onclick="goToPage(1)">1</div>
      <div class="page-btn" onclick="goToPage(2)">2</div>
      <div class="page-btn" onclick="goToPage(3)">3</div>
    </div>
  </div>

  <!-- VIOLATION: color-only indication of record status (no text/icon supplement) -->
  <style>
    .status-critical { color: red; }
    .status-normal { color: green; }
    /* Status conveyed purely by color */
  </style>

</body>
</html>
"""

# 4. Navigation menu — no aria-expanded, no keyboard handling for dropdown
nav_component_js = """\
// NavigationMenu.js
export class NavigationMenu {
  constructor(container) {
    this.container = container;
    this.render();
  }

  render() {
    const nav = document.createElement('nav');
    // VIOLATION: nav has no aria-label to distinguish from other nav regions
    
    const menuList = document.createElement('ul');
    menuList.className = 'main-menu';

    const items = [
      { label: 'Dashboard', href: '/dashboard' },
      { label: 'Appointments', href: '/appointments', children: [
        { label: 'Upcoming', href: '/appointments/upcoming' },
        { label: 'Past', href: '/appointments/past' },
      ]},
      { label: 'Records', href: '/records' },
      { label: 'Messages', href: '/messages' },
    ];

    items.forEach(item => {
      const li = document.createElement('li');
      const link = document.createElement('a');
      link.href = item.href;
      link.textContent = item.label;

      if (item.children) {
        // VIOLATION: no aria-expanded, no aria-haspopup on the trigger
        link.onclick = (e) => {
          e.preventDefault();
          submenu.style.display = submenu.style.display === 'block' ? 'none' : 'block';
          // VIOLATION: aria-expanded never toggled
        };

        const submenu = document.createElement('ul');
        submenu.className = 'submenu';
        submenu.style.display = 'none';
        // VIOLATION: submenu not keyboard accessible (no keydown handler for arrow keys)

        item.children.forEach(child => {
          const childLi = document.createElement('li');
          const childLink = document.createElement('a');
          childLink.href = child.href;
          childLink.textContent = child.label;
          childLi.appendChild(childLink);
          submenu.appendChild(childLi);
        });

        li.appendChild(link);
        li.appendChild(submenu);
      } else {
        li.appendChild(link);
      }

      menuList.appendChild(li);
    });

    nav.appendChild(menuList);
    this.container.appendChild(nav);
  }
}
"""

# 5. Page layout with missing landmark structure
dashboard_html = """\
<!DOCTYPE html>
<html>
<!-- VIOLATION: html element missing lang attribute -->
<head>
  <meta charset="UTF-8">
  <title>Patient Dashboard</title>
</head>
<body>
  <!-- VIOLATION: no skip-to-main-content link -->
  
  <div id="header">
    <!-- VIOLATION: header is a div, not <header> landmark -->
    <div id="logo">
      <img src="../assets/icons/logo.png">
      <!-- VIOLATION: logo image has no alt attribute at all -->
    </div>
    <div id="nav-container"></div>
  </div>

  <div id="sidebar">
    <!-- VIOLATION: sidebar uses div, not <aside> -->
    <h2>Quick Links</h2>
    <ul>
      <li><a href="/appointments">Appointments</a></li>
      <li><a href="/records">Records</a></li>
      <li><a href="/messages">Messages</a></li>
    </ul>
  </div>

  <div id="main-content">
    <!-- VIOLATION: main content area uses div, not <main> -->
    
    <div class="welcome-banner">
      <h2>Welcome back, John</h2>
    </div>

    <!-- VIOLATION: status cards use h4 directly under h2 (skipped h3) -->
    <h4>Upcoming Appointments</h4>
    <div class="appointment-card">
      <span>March 20, 2024 - Dr. Smith</span>
      <!-- VIOLATION: purely decorative pattern used with meaningful icon, no alt -->
      <img src="../assets/icons/calendar.png">
    </div>

    <h4>Recent Messages</h4>
    <div class="messages-list">
      <!-- VIOLATION: message items are clickable divs, not buttons or links -->
      <div class="message-item" onclick="openMessage(1)">
        <span class="msg-subject">Lab results available</span>
        <span class="msg-date">Mar 18</span>
      </div>
      <div class="message-item" onclick="openMessage(2)">
        <span class="msg-subject">Prescription renewal reminder</span>
        <span class="msg-date">Mar 16</span>
      </div>
    </div>
  </div>

  <div id="footer">
    <!-- VIOLATION: footer is a div, not <footer> landmark -->
    <p>© 2024 Patient Portal. All rights reserved.</p>
  </div>

  <script src="./NavigationMenu.js" type="module"></script>
</body>
</html>
"""

problem_files = {
    "src/pages/patient-registration.html": patient_form_html,
    "src/components/modals/AppointmentModal.js": appointment_modal_js,
    "src/components/tables/MedicalRecordsTable.html": records_table_html,
    "src/components/NavigationMenu.js": nav_component_js,
    "src/pages/dashboard.html": dashboard_html,
}

for path, content in problem_files.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print("Files created:")
for path in list(distractor_files.keys()) + list(problem_files.keys()):
    print(f"  {os.path.join(workspace, path)}")