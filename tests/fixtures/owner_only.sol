pragma solidity 0.4.24;

// Call-then-write, but only the owner (set at deployment) can reach it.
contract OwnerOnly {
    address public owner;
    uint256 public paid;

    constructor() public {
        owner = msg.sender;
    }

    function pay(address to, uint256 amount) public {
        require(msg.sender == owner);
        require(to.call.value(amount)());
        paid += amount;
    }
}
