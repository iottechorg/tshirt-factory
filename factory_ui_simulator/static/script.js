// web_app/script.js

let lastMachineData = null;
let currentMachineSensors = {}

let currentMachines = [];
let currentSensors = {};
let currentTestCases = [];
let randomProductionIntervalId = null;
let productionHistory = []; // Store production history

// Load production history from localStorage
function loadProductionHistory() {
    try {
        const stored = localStorage.getItem('productionHistory');
        if (stored) {
            productionHistory = JSON.parse(stored);
            console.log(`Loaded ${productionHistory.length} production records from localStorage`);
            renderProductionHistory();
        }
    } catch (e) {
        console.error('Error loading production history:', e);
        productionHistory = [];
    }
}

// Save production history to localStorage (keep last 20)
function saveProductionHistory() {
    try {
        // Keep only last 20 items
        if (productionHistory.length > 20) {
            productionHistory = productionHistory.slice(0, 20);
        }
        localStorage.setItem('productionHistory', JSON.stringify(productionHistory));
    } catch (e) {
        console.error('Error saving production history:', e);
    }
}

// Render production history from memory
function renderProductionHistory() {
    if (productionHistory.length === 0) return;
    
    // Create table if it doesn't exist
    if (!$('#production-table').length) {
        $('#production-results').append(
            `<div class="overflow-x-auto">
                <table id="production-table" class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Production ID</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Steps</th>
                        </tr>
                    </thead>
                    <tbody id="production-table-body" class="bg-white divide-y divide-gray-200"></tbody>
                </table>
            </div>`
        );
    }
    
    const tableBody = $('#production-table-body');
    tableBody.empty();
    
    // Render all history items
    productionHistory.forEach((item) => {
        const row = `
            <tr data-order-id="${item.orderId}">
                <td class="product-name px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.productName}</td>
                <td class="order-id px-6 py-4 whitespace-nowrap text-sm font-mono text-xs text-gray-500">${item.orderId}</td>
                <td class="status px-6 py-4 whitespace-nowrap text-sm font-medium ${item.statusClass}">${item.status}</td>
                <td class="steps px-6 py-4 text-sm text-gray-500">${item.stepInfo}</td>
            </tr>`;
        tableBody.append(row);
    });
}
function fetchMachines() {
    $.get(`${API_BASE_URL}/machines`, function(data) {
        let machineSelect = $('#machineSelect');
        let machineTableBody = $('#machine-table-body')
        let sensorSelect = $('#sensorSelect');
        let hasChanged = false;

        if (JSON.stringify(data.map(m => m.name)) !== JSON.stringify(currentMachines)) {
           machineSelect.empty();
          currentMachines =  data.map(m => m.name)
           data.forEach(machine => {
               machineSelect.append(`<option value="${machine.id}">${machine.name}</option>`);
           });
           hasChanged = true;
       }

        machineTableBody.empty();
          data.forEach(machine => {
             let sensorKeys =  Object.keys(machine.sensor_data);
              let sensor_info = sensorKeys.map((key) => `<div class="text-xs"><span class="font-medium text-gray-700">${key}:</span> <span class="text-gray-900">${machine.sensor_data[key].toFixed(2)}</span></div>`)
              
              // Add Machine Status and Failure Rate for better visibility
              let statusClass = "text-gray-900";
              if (machine.runtime_state === 'error') statusClass = "text-red-600 font-bold";
              else if (machine.runtime_state === 'busy') statusClass = "text-blue-600 font-medium";
              
              let failureRateVal = machine.failure_rate !== undefined ? (machine.failure_rate * 100).toFixed(1) + "%" : "N/A";

            machineTableBody.append(`
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 w-1/5">${machine.name}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-xs text-gray-500 font-mono w-1/6">${machine.id}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm ${statusClass} w-1/6">${machine.runtime_state || 'unknown'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 w-1/6">${failureRateVal}</td>
                    <td class="px-6 py-4 text-sm text-gray-900 w-1/3">${sensor_info.join("")}</td>
                </tr>`);
            
            if (JSON.stringify(Object.keys(machine.sensor_data)) !== JSON.stringify(currentSensors[machine.name] || [])) {
                currentSensors[machine.name] = Object.keys(machine.sensor_data);
                 hasChanged = true;
            }
         });

       lastMachineData = data
          if(hasChanged){
              machineSelect.trigger('change')
          }
    }).fail(function(error){
        console.log("Error fetching machine status:", error)
        $('#machine-status').html('<p class="text-danger">Error fetching machine status</p>');
    });
}

function updateMachineFailureRate(machineId, failureRate) {
    $.ajax({
        url: `${API_BASE_URL}/machines/${machineId}`,
        type: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify({ failure_rate: failureRate }),
        success: function(data) {
            console.log("Machine failure rate updated:", data);
           fetchMachines();
           $('#updateMachineForm').addClass('hidden');
        },
        error: function(error) {
            console.log("Error while updating machine:", error);
        }
    });
}

function updateMachineSensor(machineId, sensorName, sensorValue) {
  $.ajax({
        url: `${API_BASE_URL}/machines/sensor/${machineId}/${sensorName}`,
        type: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify({ value: sensorValue }),
        success: function(data) {
             console.log(`Machine sensor updated`, data);
        },
       error: function(error) {
          console.log("Error while updating machine sensor:", error);
       }
    });
}

function startProduction(productName, productDetails, workflowId) {
    let payload = { product_name: productName, product_details: productDetails };
    if (workflowId) {
        payload.workflow_id = workflowId;
    }
    $.ajax({
        url: `${API_BASE_URL}/production`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(payload),
        success: function(data) {
            console.log("Production started:", data);
           $('#production-status').html('<p class="text-success">Production request received.</p>');
              setTimeout(function() {
                   $('#production-status').empty()
             }, 5000);
        },
       error: function(error) {
            console.log("Error starting production:", error);
           $('#production-status').html('<p class="text-danger">Error starting production</p>');
        }
    });
}

function updateProductionConfig(successRate, failureRateMultiplier) {
     let payload = {};
      if(successRate){
          payload["success_rate"] = successRate;
      }
     if (failureRateMultiplier) {
           payload["failure_rate_multiplier"] = failureRateMultiplier;
      }
        $.ajax({
             url: `${API_BASE_URL}/production/config`,
              type: 'PUT',
             contentType: 'application/json',
              data: JSON.stringify(payload),
             success: function(data) {
                console.log("Production config updated:", data);
                 $('#production-status').html('<p class="text-success">Production config updated.</p>');
                   setTimeout(function() {
                      $('#production-status').empty()
                   }, 5000);
             },
              error: function(error){
                   console.log("Error while updating production config", error)
                   $('#production-status').html('<p class="text-danger">Error updating production config</p>');
              }
        });
 }

function fetchTestCases() {
    $.get(`${API_BASE_URL}/test_cases.json`, function(data) {
        if (!data || !data.test_cases) return;
        
        currentTestCases = data.test_cases;
        let testSelect = $('#testSelect');
        testSelect.empty();
        testSelect.append(`<option value="All">All Test Cases</option>`);
        
        currentTestCases.forEach((test, index) => {
            testSelect.append(`<option value="${test.name}">${test.name}: ${test.description}</option>`)
        });
        console.log("Loaded test cases:", currentTestCases.length);
    }).fail(function() {
        console.error("Failed to fetch test cases from server");
    });
}

function fetchWorkflows() {
    $.get(`${API_BASE_URL}/workflows`, function(data) {
        if (!data || data.length === 0) return;
        
        let workflowSelect = $('#workflowSelect');
        workflowSelect.empty();
        workflowSelect.append(`<option value="">Auto (Default)</option>`);
        
        data.forEach((workflow) => {
            let label = workflow.workflow_name;
            if (workflow.description) {
                label += ` - ${workflow.description}`;
            }
            workflowSelect.append(`<option value="${workflow.workflow_id}">${label}</option>`);
        });
        console.log("Loaded workflows:", data.length);
    }).fail(function() {
        console.log("Failed to fetch workflows from server");
    });
}

function triggerTestCase(testCaseName) {
    $.ajax({
        url: `${API_BASE_URL}/test/run/${testCaseName}`,
        type: 'POST',
        success: function(data) {
            console.log(`Test case ${testCaseName} started:`, data);
            $('#test-cases-status').html(`<p class="text-green-600">Test case <b>${testCaseName}</b> started.</p>`);
             setTimeout(function() {
                $('#test-cases-status').empty()
            }, 5000);
        },
        error: function(error){
           console.log("Error while running test case:", error)
           $('#test-cases-status').html(`<p class="text-red-600">Error: ${error.responseJSON ? error.responseJSON.message : 'failed to start test'}</p>`);
        }
    });
}

function triggerRandomTestCase() {
    $.ajax({
        url: `${API_BASE_URL}/test/random_test`,
        type: 'POST',
        success: function(data) {
           console.log("Random test case started:", data);
           $('#test-cases-status').html('<p class="text-green-600">Random test case started.</p>');
             setTimeout(function() {
                $('#test-cases-status').empty()
            }, 5000);
        },
        error: function(error){
           console.log("Error while running random test case:", error)
           $('#test-cases-status').html('<p class="text-red-600">Error while running random test case</p>');
        }
    });
}
/**
 * Open the external customizer/customer UI with a generated prompt containing
 * current factory context (machines, key sensors, production status).
 */
function openCustomizer() {
    // Fetch factory config, machines and production status in parallel
    Promise.all([
        $.get(`${API_BASE_URL}/factory-config`),
        $.get(`${API_BASE_URL}/machines`),
        $.get(`${API_BASE_URL}/production/status`)
    ]).then(function(results) {
        const factoryCfg = results[0] && results[0].factory_id ? results[0] : null;
        const machines = Array.isArray(results[1]) ? results[1] : (results[1].machines || []);
        const production = results[2] && results[2].status ? results[2] : null;

        // Build a short human-friendly prompt
        let promptParts = [];
        if (factoryCfg && factoryCfg.factory_id) {
            promptParts.push(`Factory: ${factoryCfg.factory_id}`);
        } else if (factoryCfg && factoryCfg.name) {
            promptParts.push(`Factory: ${factoryCfg.name}`);
        } else {
            promptParts.push(`Factory: ${"{{FACTORY_SITE_ID}}"}`);
        }

        if (machines && machines.length) {
            const machineSummaries = machines.map(m => {
                const sensors = Object.keys(m.sensor_data || {}).slice(0,3).map(k => `${k}=${m.sensor_data[k]}`).join(', ');
                return `${m.name || m.id}(${m.id})${sensors ? ' — ' + sensors : ''}`;
            });
            promptParts.push(`Machines: ${machineSummaries.join('; ')}`);
        }

        if (production && production.status) {
            promptParts.push(`Production status: ${production.status}`);
        }

        const prompt = `Context for product customization — ${promptParts.join(' | ')}`;
        const encoded = encodeURIComponent(prompt);

        // Open in new tab with prompt as query param
        const url = CUSTOMER_UI_URL + (CUSTOMER_UI_URL.indexOf('?') === -1 ? `?prompt=${encoded}` : `&prompt=${encoded}`);
        window.open(url, '_blank');

    }).catch(function(err){
        console.error('Failed to collect context for customizer:', err);
        // Fallback: just open the customizer root
        window.open(CUSTOMER_UI_URL, '_blank');
    });
}
function generateRandomProductName() {
    let names = ['Awesome', 'Cool', 'Stylish', 'Great', 'Modern', 'Classic'];
    let types = ['Cotton', 'Linen', 'Silk', 'Denim', 'Wool'];
   return `${randomChoice(names)} ${randomChoice(types)} T-Shirt`;
}

function generateRandomProductDetails() {
    let materials = ["Cotton", "Denim", "Polyester"];
    let sizes = ["Small", "Medium", "Large", "X-Large"];
    let stitchTypes = ["Straight", "Zigzag", "Overlock"];
    let threadColors = ["Red", "Blue", "Green", "Black", "White"];
    let ironTemps = [100, 110, 120, 130, 140, 150]
    let steamLevels = ["Low", "Medium", "High"];
//    let designNames = ["Logo1", "Logo2", "Pattern1", "None"];
    let inkTypes = ["Water-based", "Oil-based", "None"];
    return {
        material: randomChoice(materials),
        cut_size: randomChoice(sizes),
        stitch_type: randomChoice(stitchTypes),
        thread_color: randomChoice(threadColors),
        iron_temperature_setpoint:  randomChoice(ironTemps),
        steam_level: randomChoice(steamLevels),
        //design_name: randomChoice(designNames),
        ink_type: randomChoice(inkTypes)
    };
}

function randomChoice(array) {
    return array[Math.floor(Math.random() * array.length)];
}


$(document).ready(function() {

    // Load production history from localStorage on page load
    loadProductionHistory();

    fetchMachines();
    fetchTestCases();
    fetchWorkflows();
    setInterval(fetchMachines, MACHINE_DATA_REST_REQUEST_INTERVAL * 1000)

     $('#updateFailureRateBtn').click(function() {
         let machineId = $('#machineSelect').val();
       let failureRate = $('#failureRate').val();
        if (machineId && failureRate) {
            updateMachineFailureRate(machineId, failureRate);
       } else {
           alert("Please select a machine and enter failure rate!")
       }
    });
    $('#machineSelect').change(function() {
         let machineId = $(this).val();
         let sensorSelect = $('#sensorSelect');
         let sensorValueSelect = $('#sensorValue')
         sensorSelect.empty()
         sensorValueSelect.empty()
       let selectedMachine = lastMachineData.find(machine => machine.id === machineId);
      if (selectedMachine) {
         for (const key of Object.keys(selectedMachine.sensor_data)){
               sensorSelect.append(`<option value="${key}">${key}</option>`);
                  let value = selectedMachine.sensor_data[key]
                   let isNumber =  typeof value === 'number';
                    if (isNumber){
                      sensorValueSelect.append(`<option value="${value + 1}">${value+1}</option>`);
                    sensorValueSelect.append(`<option value="${value}">${value}</option>`);
                     sensorValueSelect.append(`<option value="${value - 1}">${value-1}</option>`);
                  }else{
                     sensorValueSelect.append(`<option value="${value}">${value}</option>`);
                  }
            }
        }
    });

    $('#updateSensorBtn').click(function() {
       let machineId = $('#machineSelect').val();
       let sensorName = $('#sensorSelect').val();
       let sensorValue = $('#sensorValue').val();
       if(machineId && sensorName && sensorValue){
            updateMachineSensor(machineId, sensorName, sensorValue);
        }else{
            alert("Please select a machine, a sensor name, a sensor value and a time!")
        }
    });
    $('#startProductionBtn').click(function() {
        let productName = $('#productName').val();
        let workflowId = $('#workflowSelect').val();
        let productDetails = null;
        try{
            if(productDetailsStr){
              productDetails = JSON.parse(productDetailsStr)
           }
           startProduction(productName, productDetails, workflowId
           startProduction(productName, productDetails);
       }catch(e){
           alert("Please enter a valid JSON");
        }
    });
    $('#generateProductNameBtn').click(function(){
        let name = generateRandomProductName()
        $('#productName').val(name)
    });
     $('#generateProductDetailsBtn').click(function(){
        let details = generateRandomProductDetails()
      $('#productDetails').val(JSON.stringify(details, null, 2))
    });
    $('#updateProductionConfigBtn').click(function() {
       let successRate = $('#productionSuccessRate').val();
       let failureRateMultiplier = $('#failureRateMultiplier').val();
        if(successRate || failureRateMultiplier){
            updateProductionConfig(successRate, failureRateMultiplier);
       }else {
           alert("Please enter a valid value!")
       }
    });
    $('#runTestCaseBtn').click(function() {
       let testCaseValue = $('#testSelect').val();
       if(testCaseValue === "All"){
            if (currentTestCases.length > 0) {
                currentTestCases.forEach(tc => {
                    triggerTestCase(tc.name);
                });
            }
       } else if (testCaseValue) {
           triggerTestCase(testCaseValue);
       } else {
           alert("Please select a test case!");
       }
    });
    $('#generateRandomTestCaseBtn').click(function() {
       triggerRandomTestCase();
    });
    $('#clearProductionResultsBtn').click(function() {
         $('#production-table-body').empty();
    });
    let randomProductionIntervalId = null;
    $('#startRandomProductionBtn').click(function() {
        let interval = parseInt($('#randomProductionInterval').val()) * 1000
           $('#startRandomProductionBtn').prop("disabled", true);
           $('#stopRandomProductionBtn').prop("disabled", false);
        randomProductionIntervalId = setInterval(function() {
            let productDetails = generateRandomProductDetails();
             let productName = generateRandomProductName()
            startProduction(productName, productDetails)
        }, interval);
    });
    $('#stopRandomProductionBtn').click(function() {
       clearInterval(randomProductionIntervalId);
        $('#startRandomProductionBtn').prop("disabled", false);
        $('#stopRandomProductionBtn').prop("disabled", true);
   });

   const client = new Paho.MQTT.Client(MQTT_BROKER, Number(MQTT_WS_PORT), "web_" + parseInt(Math.random() * 100000, 10));
    client.onConnectionLost = onConnectionLost;
    client.onMessageArrived = onMessageArrived;
       client.connect({
         onSuccess: onConnect,
           useSSL: false,
      });
    function onConnect() {
         console.log("MQTT Connected");
         client.subscribe(MQTT_TOPIC_PRODUCTION);
         client.subscribe(`factory/${FACTORY_SITE_ID}/test/status`);
     }
     function onConnectionLost(responseObject) {
        console.log("MQTT Connection Lost: "+responseObject.errorMessage)
    }
    function onMessageArrived(message) {
        let payload;
        try{
           payload = JSON.parse(message.payloadString);
        } catch(e){
          return;
        }

        const topic = message.destinationName;
        
        // Handle Test Status Updates
        if (topic.endsWith('/test/status')) {
            console.log("Test progress update:", payload);
            let statusHtml = "";
            if (payload.status === "running") {
                const pct = Math.round(((payload.step_index + 1) / payload.total_steps) * 100);
                statusHtml = `
                    <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
                        <p class="text-blue-700 font-medium">Running Test: ${payload.test_name}</p>
                        <div class="mt-2 w-full bg-gray-200 rounded-full h-2.5">
                            <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${pct}%"></div>
                        </div>
                        <p class="text-xs text-blue-500 mt-1">Step ${payload.step_index + 1} of ${payload.total_steps}: ${payload.action}</p>
                    </div>`;
            } else if (payload.status === "completed") {
                statusHtml = `<p class="text-green-600 font-bold p-2 bg-green-50 rounded">✓ Test <b>${payload.test_name}</b> completed successfully!</p>`;
                setTimeout(() => $('#test-cases-status').empty(), 5000);
            } else if (payload.status === "error") {
                statusHtml = `<p class="text-red-600 font-bold p-2 bg-red-50 rounded">✗ Test <b>${payload.test_name}</b> failed: ${payload.error}</p>`;
            }
            $('#test-cases-status').html(statusHtml);
            return;
        }

        // Handle Production Updates (existing logic)
        console.log("Production data received:", payload);
        const productionData = payload;
        const orderId = productionData["order_id"] || productionData["production_id"] || "-";
        const productName = productionData["product_name"] || "-";
        const status = productionData["status"] || "-";
        const steps = productionData["step_results"] || productionData["steps"] || null;
        
        let tableBody = $('#production-table-body')
        if (!$('#production-table').length){
          $('#production-results').append(
           `<div class="overflow-x-auto">
               <table id="production-table" class="min-w-full divide-y divide-gray-200">
                   <thead class="bg-gray-50">
                      <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
                           <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Production ID</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Steps</th>
                       </tr>
                   </thead>
                    <tbody id="production-table-body" class="bg-white divide-y divide-gray-200"></tbody>
               </table>
           </div>`
          );
           tableBody = $('#production-table-body')
        }
        
        // Determine status class
        const statusClass = status === 'failed' ? 'text-red-600' : (status === 'completed' || status === 'success' ? 'text-green-600' : 'text-blue-600');
        const stepInfo = steps ? steps.map((s) => ` ${s.operation || 'unknown'}: ${s.status}`).join(",") : "Processing...";
        
        // Find existing entry in history
        const historyIndex = productionHistory.findIndex(item => item.orderId === orderId);
        
        if (historyIndex >= 0) {
            // Update existing entry
            productionHistory[historyIndex].productName = productName !== "-" ? productName : productionHistory[historyIndex].productName;
            productionHistory[historyIndex].status = status;
            productionHistory[historyIndex].statusClass = statusClass;
            productionHistory[historyIndex].stepInfo = stepInfo;
        } else {
            // Add new entry at the beginning
            productionHistory.unshift({
                orderId: orderId,
                productName: productName,
                status: status,
                statusClass: statusClass,
                stepInfo: stepInfo,
                timestamp: Date.now()
            });
        }
        
        // Keep only last 20 items
        if (productionHistory.length > 20) {
            productionHistory = productionHistory.slice(0, 20);
        }
        
        // Save to localStorage
        saveProductionHistory();
        
        // Update or add row in the table
        let existingRow = $(`tr[data-order-id="${orderId}"]`);
        
        if (existingRow.length) {
            // Update existing row
            if (productName !== "-") existingRow.find('.product-name').text(productName);
            existingRow.find('.status').text(status)
                .removeClass('text-red-600 text-green-600 text-blue-600')
                .addClass(statusClass);
            existingRow.find('.steps').text(stepInfo);
        } else {
            // Add new row
            let row = `
              <tr data-order-id="${orderId}">
                  <td class="product-name px-6 py-4 whitespace-nowrap text-sm text-gray-900">${productName}</td>
                   <td class="order-id px-6 py-4 whitespace-nowrap text-sm font-mono text-xs text-gray-500">${orderId}</td>
                  <td class="status px-6 py-4 whitespace-nowrap text-sm font-medium ${statusClass}">${status}</td>
                 <td class="steps px-6 py-4 text-sm text-gray-500">${stepInfo}</td>
               </tr>`;
            tableBody.prepend(row);
        }

        // Limit visible rows to 20
        const maxRows = 20;
        const rows = tableBody.find('tr');
        if (rows.length > maxRows) {
            rows.slice(maxRows).remove();
        }
     }
});

// ===== NEW AUTOMATION FEATURES =====

let productionAutomationRunning = false;

// Generate and run random test
function generateAndRunRandomTest() {
    $.ajax({
        url: `${API_BASE_URL}/test/generate_random`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ condition_type: null }), // Let server pick random
        success: function(data) {
            console.log("Random test generated and started:", data);
            showTestStatus("✓ Random test started: " + data.test_case.name, "success");
        },
        error: function(error) {
            console.log("Error generating random test:", error);
            showTestStatus("✗ Error generating random test", "error");
        }
    });
}

// Start random production
function startRandomProduction(intervalSeconds) {
    $.ajax({
        url: `${API_BASE_URL}/automation/production/start`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ interval_seconds: intervalSeconds }),
        success: function(data) {
            console.log("Production automation started:", data);
            productionAutomationRunning = true;
            $('#startRandomProductionBtn').prop('disabled', true).addClass('opacity-50 cursor-not-allowed');
            $('#stopRandomProductionBtn').prop('disabled', false).removeClass('opacity-50 cursor-not-allowed').addClass('bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700');
            showTestStatus(`✓ Random production started (interval: ${intervalSeconds}s)`, "success");
        },
        error: function(error) {
            console.log("Error starting production automation:", error);
            showTestStatus("✗ Error starting random production", "error");
        }
    });
}

// Stop random production
function stopRandomProduction() {
    $.ajax({
        url: `${API_BASE_URL}/automation/production/stop`,
        type: 'POST',
        success: function(data) {
            console.log("Production automation stopped:", data);
            productionAutomationRunning = false;
            $('#startRandomProductionBtn').prop('disabled', false).removeClass('opacity-50 cursor-not-allowed');
            $('#stopRandomProductionBtn').prop('disabled', true).addClass('opacity-50 cursor-not-allowed').removeClass('bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700').addClass('bg-gray-400');
            showTestStatus(`✓ Random production stopped (total: ${data.total_requests} requests)`, "success");
        },
        error: function(error) {
            console.log("Error stopping production automation:", error);
            showTestStatus("✗ Error stopping random production", "error");
        }
    });
}

// Clear production results and stop automation
function clearProductionResults() {
    $.ajax({
        url: `${API_BASE_URL}/automation/production/clear`,
        type: 'POST',
        success: function(data) {
            console.log("Production automation cleared:", data);
            productionAutomationRunning = false;
            $('#production-table-body').empty();
            
            // Clear production history from memory and localStorage
            productionHistory = [];
            localStorage.removeItem('productionHistory');
            
            $('#startRandomProductionBtn').prop('disabled', false).removeClass('opacity-50 cursor-not-allowed');
            $('#stopRandomProductionBtn').prop('disabled', true).addClass('opacity-50 cursor-not-allowed').addClass('bg-gray-400');
            showTestStatus("✓ Production results cleared", "success");
        },
        error: function(error) {
            console.log("Error clearing production results:", error);
            showTestStatus("✗ Error clearing production results", "error");
        }
    });
}

// Show test/automation status message
function showTestStatus(message, type) {
    const statusDiv = $('#test-cases-status');
    const className = type === 'success' ? 'bg-green-50 text-green-800 border-green-200' : 
                      type === 'error' ? 'bg-red-50 text-red-800 border-red-200' : 
                      'bg-blue-50 text-blue-800 border-blue-200';
    
    const html = `
        <div class="bg-white rounded-lg shadow-md p-4 border-l-4 ${className}">
            <p class="font-semibold">${message}</p>
        </div>
    `;
    
    statusDiv.html(html);
    setTimeout(() => {
        statusDiv.fadeOut(500, function() { $(this).html(''); $(this).show(); });
    }, 4000);
}

// Event handlers
$(document).ready(function() {
    // Random test button
    $('#generateRandomTestCaseBtn').click(function() {
        generateAndRunRandomTest();
    });
    
    // Random production buttons
    $('#startRandomProductionBtn').click(function() {
        const interval = parseInt($('#randomProductionInterval').val()) || 5;
        startRandomProduction(interval);
    });
    
    $('#stopRandomProductionBtn').click(function() {
        stopRandomProduction();
    });
    
    $('#clearProductionResultsBtn').click(function() {
        clearProductionResults();
    });
});
