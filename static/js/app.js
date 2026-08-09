javascript;
document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menuToggle");
  const navLinks = document.getElementById("navLinks");

  const form = document.getElementById("partnerRegistration");
  const steps = document.querySelectorAll(".form-step");
  const stepIndicators = document.querySelectorAll(".process-step");

  const backButton = document.getElementById("backButton");
  const nextButton = document.getElementById("nextButton");
  const submitButton = document.getElementById("submitButton");

  const sectorCheckboxes = document.querySelectorAll('input[name="sectors"]');
  const sectorError = document.getElementById("sectorError");

  const applicationCard = document.getElementById("applicationCard");
  const submissionSuccess = document.getElementById("submissionSuccess");
  const applicationReference = document.getElementById("applicationReference");

  const portalEmpty = document.getElementById("portalEmpty");
  const partnerDashboard = document.getElementById("partnerDashboard");
  const dashboardOrgName = document.getElementById("dashboardOrgName");
  const dashboardReference = document.getElementById("dashboardReference");
  const dashboardSectors = document.getElementById("dashboardSectors");
  const dashboardDate = document.getElementById("dashboardDate");
  const dashboardDocuments = document.getElementById("dashboardDocuments");

  let currentStep = 1;

  /* Mobile navigation */
  menuToggle.addEventListener("click", () => {
    const isOpen = navLinks.classList.toggle("open");
    menuToggle.setAttribute("aria-expanded", isOpen);
    menuToggle.textContent = isOpen ? "✕" : "☰";
  });

  document.querySelectorAll(".nav-links a").forEach((link) => {
    link.addEventListener("click", () => {
      navLinks.classList.remove("open");
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.textContent = "☰";
    });
  });

  /* Registration wizard */
  function showStep(stepNumber) {
    currentStep = stepNumber;

    steps.forEach((step) => {
      const stepValue = Number(step.dataset.step);
      step.hidden = stepValue !== currentStep;
      step.classList.toggle("active", stepValue === currentStep);
    });

    stepIndicators.forEach((indicator) => {
      const indicatorNumber = Number(indicator.dataset.stepIndicator);

      indicator.classList.toggle("active", indicatorNumber === currentStep);
      indicator.classList.toggle("completed", indicatorNumber < currentStep);
    });

    backButton.disabled = currentStep === 1;

    if (currentStep === 4) {
      nextButton.hidden = true;
      submitButton.hidden = false;
    } else {
      nextButton.hidden = false;
      submitButton.hidden = true;
    }
  }

  function validateSectorSelection() {
    const selectedSector = Array.from(sectorCheckboxes).some(
      (checkbox) => checkbox.checked,
    );

    sectorError.hidden = selectedSector;
    return selectedSector;
  }

  function validateCurrentStep() {
    const currentPanel = document.querySelector(
      `.form-step[data-step="${currentStep}"]`,
    );
    const requiredFields = currentPanel.querySelectorAll("[required]");

    for (const field of requiredFields) {
      if (!field.checkValidity()) {
        field.reportValidity();
        return false;
      }
    }

    if (currentStep === 2 && !validateSectorSelection()) {
      sectorError.scrollIntoView({ behavior: "smooth", block: "center" });
      return false;
    }

    return true;
  }

  nextButton.addEventListener("click", () => {
    if (validateCurrentStep() && currentStep < 4) {
      showStep(currentStep + 1);
    }
  });

  backButton.addEventListener("click", () => {
    if (currentStep > 1) {
      showStep(currentStep - 1);
    }
  });

  sectorCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", validateSectorSelection);
  });

  /* File upload validation */
  const allowedExtensions = ["pdf", "doc", "docx", "jpg", "jpeg", "png"];
  const maxFileSize = 10 * 1024 * 1024; // 10 MB

  document.querySelectorAll(".file-input").forEach((input) => {
    input.addEventListener("change", (event) => {
      const file = event.target.files[0];
      const fileNameDisplay = document.querySelector(
        `[data-file-name="${input.id}"]`,
      );

      if (!file) {
        if (fileNameDisplay) {
          fileNameDisplay.textContent = "No file selected";
          fileNameDisplay.classList.remove("file-selected", "file-invalid");
        }
        return;
      }

      const extension = file.name.split(".").pop().toLowerCase();

      if (!allowedExtensions.includes(extension)) {
        input.value = "";

        if (fileNameDisplay) {
          fileNameDisplay.textContent =
            "Invalid file type. Use PDF, DOC, DOCX, JPG or PNG.";
          fileNameDisplay.classList.remove("file-selected");
          fileNameDisplay.classList.add("file-invalid");
        }

        return;
      }

      if (file.size > maxFileSize) {
        input.value = "";

        if (fileNameDisplay) {
          fileNameDisplay.textContent =
            "File is too large. Maximum size is 10MB.";
          fileNameDisplay.classList.remove("file-selected");
          fileNameDisplay.classList.add("file-invalid");
        }

        return;
      }

      if (fileNameDisplay) {
        fileNameDisplay.textContent = `✓ ${file.name}`;
        fileNameDisplay.classList.remove("file-invalid");
        fileNameDisplay.classList.add("file-selected");
      }
    });
  });

  /* Form submission */
  form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!validateCurrentStep()) {
      return;
    }

    const organisationName = document
      .getElementById("organisationName")
      .value.trim();
    const acronym = document.getElementById("acronym").value.trim();
    const sectors = Array.from(sectorCheckboxes)
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.value);

    const documents = [
      {
        label: "RRC Registration Certificate",
        inputId: "rrcCertificate",
      },
      {
        label: "Organisational Policies / Constitution",
        inputId: "orgPolicies",
      },
      {
        label: "Executive Director CV",
        inputId: "executiveDirectorCV",
      },
      {
        label: "Head of Programme CV",
        inputId: "headProgramCV",
      },
    ].map((document) => {
      const fileInput = document.getElementById(document.inputId);
      return {
        label: document.label,
        fileName: fileInput.files[0] ? fileInput.files[0].name : "Not uploaded",
      };
    });

    const optionalMoGEIFile =
      document.getElementById("moGEIRegistration").files[0];

    if (optionalMoGEIFile) {
      documents.push({
        label: "MoGEI Partner Coordination Registration Acknowledgement",
        fileName: optionalMoGEIFile.name,
      });
    }

    const randomNumber = Math.floor(100000 + Math.random() * 900000);
    const referenceNumber = `NDCI-2026-${randomNumber}`;

    const applicationData = {
      organisationName,
      acronym,
      referenceNumber,
      sectors,
      documents,
      submittedAt: new Date().toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      }),
    };

    /*
          For demonstration only:
          Stores basic data in browser localStorage.
          Actual documents are NOT stored in localStorage.
          Flask will later receive files using FormData.
        */
    localStorage.setItem("ndciApplication", JSON.stringify(applicationData));

    applicationReference.textContent = referenceNumber;
    form.hidden = true;
    submissionSuccess.hidden = false;

    renderPartnerDashboard();

    submissionSuccess.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  });

  /* Render portal dashboard */
  function renderPartnerDashboard() {
    const savedApplication = localStorage.getItem("ndciApplication");

    if (!savedApplication) {
      portalEmpty.hidden = false;
      partnerDashboard.hidden = true;
      return;
    }

    const application = JSON.parse(savedApplication);

    portalEmpty.hidden = true;
    partnerDashboard.hidden = false;

    dashboardOrgName.textContent = application.acronym
      ? `${application.organisationName} (${application.acronym})`
      : application.organisationName;

    dashboardReference.textContent = `Reference: ${application.referenceNumber}`;
    dashboardDate.textContent = application.submittedAt;

    dashboardSectors.innerHTML = "";
    application.sectors.forEach((sector) => {
      const tag = document.createElement("span");
      tag.className = "sector-tag";
      tag.textContent = sector;
      dashboardSectors.appendChild(tag);
    });

    dashboardDocuments.innerHTML = "";

    application.documents.forEach((document) => {
      const row = document.createElement("div");
      row.className = "document-row";

      const documentName = document.createElement("span");
      documentName.className = "document-name";
      documentName.textContent = `${document.label}: ${document.fileName}`;

      const status = document.createElement("span");
      status.className = "document-status";
      status.textContent = "✓ Submitted";

      row.appendChild(documentName);
      row.appendChild(status);

      dashboardDocuments.appendChild(row);
    });
  }

  renderPartnerDashboard();
});
