  window.addEventListener("contextmenu", function(e) {
  console.log("Context menu event triggered");
    e.preventDefault(); // Prevent the default browser context menu

    // Get the target element (the element that was clicked)
    const targetElement = e.target;

    // Log or use the target element's ID or any other property you want
    console.log("Right-clicked element ID:", targetElement.id);

    // You can pass this information to your HTMX request
    const menu = document.getElementById('custom-menu');
    menu.style.top = `${e.clientY}px`;
    menu.style.left = `${e.clientX}px`;

    // Trigger HTMX request to load the menu content
    htmx.ajax('GET', `/get-context-menu?elementId=${targetElement.id}&top=${e.clientY}&left=${e.clientX}`, {
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