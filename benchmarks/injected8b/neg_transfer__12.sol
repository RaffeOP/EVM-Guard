pragma solidity 0.8.20;

contract Bank7975 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(deposits[msg.sender] >= amount);
        payable(msg.sender).transfer(amount);
        deposits[msg.sender] -= amount;
        total -= amount;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
