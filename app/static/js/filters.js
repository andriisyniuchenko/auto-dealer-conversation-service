// Dynamic filter dropdowns: condition → make → model, year
// filterData and currentFilters must be defined before this script is loaded.

function getMakes(condition) {
  if (!condition) {
    const all = new Set();
    for (const cond of ["new", "used"])
      for (const make of Object.keys(filterData[cond] || {})) all.add(make);
    return [...all].sort();
  }
  return Object.keys(filterData[condition] || {}).sort();
}

function getModels(condition, make) {
  if (!make) return [];
  if (!condition) {
    const all = new Set();
    for (const cond of ["new", "used"])
      for (const m of (filterData[cond]?.[make]?.models || [])) all.add(m);
    return [...all].sort();
  }
  return (filterData[condition]?.[make]?.models || []).slice().sort();
}

function getYears(condition, make) {
  if (make && condition)
    return (filterData[condition]?.[make]?.years || []).slice().sort((a, b) => b - a);
  if (make) {
    const all = new Set();
    for (const cond of ["new", "used"])
      for (const y of (filterData[cond]?.[make]?.years || [])) all.add(y);
    return [...all].sort((a, b) => b - a);
  }
  if (condition)
    return (filterData._years?.[condition] || []).slice();
  const all = new Set([...(filterData._years?.new || []), ...(filterData._years?.used || [])]);
  return [...all].sort((a, b) => b - a);
}

function populateSelect(selectEl, values, selectedValue) {
  const current = selectEl.value;
  selectEl.innerHTML = '<option value="">Any</option>';
  for (const v of values) {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    if (String(v) === String(selectedValue || current)) opt.selected = true;
    selectEl.appendChild(opt);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const conditionEl = document.getElementById("conditionSelect");
  const makeEl = document.getElementById("makeSelect");
  const modelEl = document.getElementById("modelSelect");
  const yearEl = document.getElementById("yearSelect");

  function refresh(keepMake, keepModel, keepYear) {
    const condition = conditionEl.value;
    const make = keepMake ? makeEl.value : "";
    populateSelect(makeEl, getMakes(condition), keepMake ? make : currentFilters.make);
    populateSelect(modelEl, getModels(condition, makeEl.value), keepModel ? modelEl.value : currentFilters.model);
    populateSelect(yearEl, getYears(condition, makeEl.value), keepYear ? yearEl.value : currentFilters.year);
  }

  conditionEl.addEventListener("change", () => refresh(false, false, false));
  makeEl.addEventListener("change", () => {
    populateSelect(modelEl, getModels(conditionEl.value, makeEl.value), "");
    populateSelect(yearEl, getYears(conditionEl.value, makeEl.value), "");
  });

  // Init with current URL filter values
  refresh(true, true, true);
});