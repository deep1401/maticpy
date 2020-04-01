from web3 import Web3
import json
from solc import compile_standard

#w3 = Web3(HTTPProvider('http://localhost:8545'))
#airbnbContractAddress = '0x5c5483b44B29C6CD2338E95588089765D59Cbd6E'

compiled_sol = compile_standard({
     "language": "Solidity",
     "sources": {
         "Airbnb.sol": {
             "content": '''
                 pragma solidity ^0.5.7;

contract Airbnb {

  // Property to be rented out on Airbnb
  struct Property {
    string name;
    string description;
    bool isActive; // is property active
    uint256 price; // per day price in wei (1 ether = 10^18 wei)
    address owner; // Owner of the property
    // Is the property booked on a particular day,
    // For the sake of simplicity, we assign 0 to Jan 1, 1 to Jan 2 and so on
    // so isBooked[31] will denote whether the property is booked for Feb 1
    bool[] isBooked;
  }

  uint256 public propertyId;

  // mapping of propertyId to Property object
  mapping(uint256 => Property) public properties;

  // Details of a particular booking
  struct Booking {
    uint256 propertyId;
    uint256 checkInDate;
    uint256 checkoutDate;
    address user;
  }

  uint256 public bookingId;

  // mapping of bookingId to Booking object
  mapping(uint256 => Booking) public bookings;

  // This event is emitted when a new property is put up for sale
  event NewProperty (
    uint256 indexed propertyId
  );

  // This event is emitted when a NewBooking is made
  event NewBooking (
    uint256 indexed propertyId,
    uint256 indexed bookingId
  );

  /**
   * @dev Put up an Airbnb property in the market
   * @param name Name of the property
   * @param description Short description of your property
   * @param price Price per day in wei (1 ether = 10^18 wei)
   */
  function rentOutproperty(string memory name, string memory description, uint256 price) public {
    Property memory property = Property(name, description, true /* isActive */, price, msg.sender /* owner */, new bool[](365));

    // Persist `property` object to the "permanent" storage
    properties[propertyId] = property;

    // emit an event to notify the clients
    emit NewProperty(propertyId++);
  }

  /**
   * @dev Make an Airbnb booking
   * @param _propertyId id of the property to rent out
   * @param checkInDate Check-in date
   * @param checkoutDate Check-out date
   */
  function rentProperty(uint256 _propertyId, uint256 checkInDate, uint256 checkoutDate) public payable {
    // Retrieve `property` object from the storage
    Property storage property = properties[_propertyId];

    // Assert that property is active
    require(
      property.isActive == true,
      "property with this ID is not active"
    );

    // Assert that property is available for the dates
    for (uint256 i = checkInDate; i < checkoutDate; i++) {
      if (property.isBooked[i] == true) {
        // if property is booked on a day, revert the transaction
        revert("property is not available for the selected dates");
      }
    }

    // Check the customer has sent an amount equal to (pricePerDay * numberOfDays)
    require(
      msg.value == property.price * (checkoutDate - checkInDate),
      "Sent insufficient funds"
    );

    // send funds to the owner of the property
    _sendFunds(property.owner, msg.value);

    // conditions for a booking are satisfied, so make the booking
    _createBooking(_propertyId, checkInDate, checkoutDate);
  }

  function _createBooking(uint256 _propertyId, uint256 checkInDate, uint256 checkoutDate) internal {
    // Create a new booking object
    bookings[bookingId] = Booking(_propertyId, checkInDate, checkoutDate, msg.sender);

    // Retrieve `property` object from the storage
    Property storage property = properties[_propertyId];

    // Mark the property booked on the requested dates
    for (uint256 i = checkInDate; i < checkoutDate; i++) {
      property.isBooked[i] = true;
    }

    // Emit an event to notify clients
    emit NewBooking(_propertyId, bookingId++);
  }

  function _sendFunds (address beneficiary, uint256 value) internal {
    // address(uint160()) is a weird solidity quirk
    // Read more here: https://solidity.readthedocs.io/en/v0.5.10/050-breaking-changes.html?highlight=address%20payable#explicitness-requirements
    address(uint160(beneficiary)).transfer(value);
  }

  /**
   * @dev Take down the property from the market
   * @param _propertyId Property ID
   */
  function markPropertyAsInactive(uint256 _propertyId) public {
    require(
      properties[_propertyId].owner == msg.sender,
      "THIS IS NOT YOUR PROPERTY"
    );
    properties[_propertyId].isActive = false;
  }
}
               '''
         }
     },
     "settings":
         {
             "outputSelection": {
                 "*": {
                     "*": [
                         "metadata", "evm.bytecode"
                         , "evm.bytecode.sourceMap"
                     ]
                }
            }
        }
})


# web3.py instance
w3 = Web3(Web3.EthereumTesterProvider())
# set pre-funded account as sender
w3.eth.defaultAccount = w3.eth.accounts[0]
# get bytecode
bytecode = compiled_sol['contracts']['Airbnb.sol']['Airbnb']['evm']['bytecode']['object']
# get abi
abi = json.loads(compiled_sol['contracts']['Airbnb.sol']['Airbnb']['metadata'])['output']['abi']

Greeter = w3.eth.contract(abi=abi, bytecode=bytecode)
# Submit the transaction that deploys the contract
tx_hash = Greeter.constructor().transact()
# Wait for the transaction to be mined, and get the transaction receipt
tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
greeter = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

tx_hash = greeter.functions.rentOutproperty('Jay Heights','1 BHK', 25000).transact()