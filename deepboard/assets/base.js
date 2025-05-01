  window.addEventListener("contextmenu", function(e) {
    // Get the target element (the element that was clicked)
    let element = e.target;

    e.preventDefault(); // Prevent the default browser context menu
    const ids = [];

      while (element) {
          if (element.id) {
              ids.push(element.id);
          }
          element = element.parentElement;
      }

    // You can pass this information to your HTMX request
    const menu = document.getElementById('custom-menu');
    menu.style.top = `${e.clientY}px`;
    menu.style.left = `${e.clientX}px`;

    // Trigger HTMX request to load the menu content
    // Join ids with ,
    str_ids = ids.join(",")
    htmx.ajax('GET', `/get-context-menu?elementIds=${str_ids}&top=${e.clientY}&left=${e.clientX}`, {
      target: '#custom-menu',
      swap: 'outerHTML',  // Correct usage of swap attribute
      headers: {
        'HX-Swap-OOB': 'true'  // Use correct OOB header for out-of-band swaps
      }
    });
  });

  // Hide the menu when clicking elsewhere
  window.addEventListener("click", () => {
    const menu = document.getElementById('custom-menu');
    menu.style.visibility = "hidden";
  });


function copyToClipboard(container) {
    const text = container.querySelector('.copy-text').innerText;

    navigator.clipboard.writeText(text).then(() => {
      container.classList.add('copied');
      setTimeout(() => {
        container.classList.remove('copied');
      }, 1200);
    });
}

// function enableShiftClickTrigger(){
//   document.addEventListener('click', function (event) {
//     if (event.shiftKey) {
//       // Only trigger HTMX on elements that explicitly want it
//       let target = event.target.closest('[hx-trigger~="shiftclick"]');
//       if (target) {
//         htmx.trigger(target, 'shiftclick');
//       }
//     }
//   });
// }
// enableShiftClickTrigger();

function shiftClickDataGrid(event){
    const el = event.target.closest('.table-row');
    if (!el) return; // Not one of ours
    if (event.shiftKey) {
      const originalUrl = el.getAttribute('hx-get'); // e.g. "/default-endpoint?runID=3"
      const url = new URL(originalUrl, window.location.origin); // create full URL to parse
      const params = url.search;

     // Instead of modifying the attribute, trigger htmx manually with the new URL
      htmx.ajax('GET', `/shift_click_row${params}`, {target: el.getAttribute('hx-target') || el});

      // Prevent the original click handler from firing
      event.preventDefault();
      event.stopPropagation();
    }
}
document.addEventListener('click', shiftClickDataGrid);