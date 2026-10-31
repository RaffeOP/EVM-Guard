pragma solidity 0.5.12;

contract Escrow2947 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(deposits[msg.sender] >= amount);
        msg.sender.transfer(amount);
        deposits[msg.sender] -= amount;
        total -= amount;
    }

    function ownerOf_() public view returns (address) { return owner; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
