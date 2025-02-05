// web_app/script.js

let lastMachineData = null;
let currentMachineSensors = {}

let currentMachines = [];
let currentSensors = {};
let randomProductionIntervalId = null;
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
              let sensor_info = sensorKeys.map((key) => ` ${key}: ${machine.sensor_data[key]} `)
            machineTableBody.append(`<tr><td>${machine.name}</td><td>${machine.id}</td><td>${sensor_info.join(" , ")}</td></tr>`);
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
           $('#updateMachineForm').collapse('hide');
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

function startProduction(productName, productDetails) {
    $.ajax({
        url: `${API_BASE_URL}/production`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ product_name: productName, product_details: productDetails }),
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
    $.ajax({
        url: "test_cases.json",
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            let testSelect = $('#testSelect');
            testSelect.empty();
              testSelect.append(`<option value="All">All</option>`);
            data.test_cases.forEach((test, index) => {
                testSelect.append(`<option value="${index}">${test.name}: ${test.description}</option>`)
            })
        },
       error: function(error) {
           console.log("Error loading test cases:", error);
           $('#test-cases-status').html('<p class="text-danger">Error loading test cases</p>');
        }
    });
}

function triggerTestCase(testCaseName) {
    $.ajax({
        url: `${API_BASE_URL}/test/${testCaseName}`,
        type: 'POST',
        success: function(data) {
           console.log("Test case started:", data);
            $('#test-cases-status').html('<p class="text-success">Test case started.</p>');
           setTimeout(function() {
               $('#test-cases-status').empty()
           }, 5000);
        },
       error: function(error){
         console.log("Error while running test case:", error)
          $('#test-cases-status').html('<p class="text-danger">Error running test case</p>');
        }
    });
}

function triggerRandomTestCase() {
    $.ajax({
        url: `${API_BASE_URL}/test/random_test`,
        type: 'POST',
        success: function(data) {
           console.log("Random test case started:", data);
           $('#random-test-status').html('<p class="text-success">Random test case started.</p>');
             setTimeout(function() {
                $('#random-test-status').empty()
            }, 5000);
        },
        error: function(error){
           console.log("Error while running random test case:", error)
           $('#random-test-status').html('<p class="text-danger">Error while running random test case</p>');
        }
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

    fetchMachines();
    fetchTestCases();
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
        let productDetailsStr = $('#productDetails').val();
        let productDetails = null;
        try{
            if(productDetailsStr){
              productDetails = JSON.parse(productDetailsStr)
           }
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
       let testCaseName = $('#testSelect').val();
      if(testCaseName == "All"){
            $.ajax({
                    url: "test_cases.json",
                    type: 'GET',
                     dataType: 'json',
                     success: function(data) {
                       if(data && data.test_cases){
                         data.test_cases.forEach(test => {
                            triggerTestCase(test.name);
                      });
                     }
                  },
                    error: function(error) {
                       console.log("Error while loading test cases:", error)
                        $('#test-cases-status').html('<p class="text-danger">Error while running test case!</p>');
                    }
           });
       }else {
           $.ajax({
               url: "test_cases.json",
                type: 'GET',
               dataType: 'json',
                success: function(data) {
                   if (data && data.test_cases) {
                       let testIndex = $('#testSelect').val();
                       if (data.test_cases[testIndex]) {
                         triggerTestCase(data.test_cases[testIndex].name);
                     }
                   }else {
                         console.log("Test case not found!");
                      $('#test-cases-status').html('<p class="text-danger">Test case not found!</p>');
                  }
                },
                 error: function(error) {
                     console.log("Error while loading test cases:", error)
                     $('#test-cases-status').html('<p class="text-danger">Error while running test case!</p>');
                }
            });
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
     }
     function onConnectionLost(responseObject) {
        console.log("MQTT Connection Lost: "+responseObject.errorMessage)
    }
    function onMessageArrived(message) {
        let productionData;
        try{
           productionData = JSON.parse(message.payloadString);
      } catch(e){
          return;
       }

        console.log("Production data received:", productionData);
       let table = $('#production-table')
        let tableBody = $('#production-table-body')
       if (!table.length){
          $('#tests').append(
           `<table id="production-table" class="table table-striped mt-3">
               <thead>
                  <tr>
                    <th>Test Name</th>
                       <th>Product Id</th>
                    <th>Result</th>
                    <th>Data</th>
                   </tr>
               </thead>
                <tbody id="production-table-body"></tbody>
           </table>`
          );
           tableBody = $('#production-table-body')
        }
        let step_information =  productionData["steps"] ? productionData["steps"].map((s) => ` Step: ${s.name} status: ${s.status}`).join(",") : ""
        let row = `
              <tr>
                  <td>${productionData["product_name"] || "-"}</td>
                   <td>${productionData["production_id"] || "-"}</td>
                  <td>${productionData["status"] || "-"}</td>
                 <td> ${step_information} </td>
                </tr>`;
         tableBody.prepend(row)
         const maxRows = 10;
         const rows = tableBody.find('tr');
           if (rows.length > maxRows) {
                rows.slice(maxRows).remove();
            }
     }
});