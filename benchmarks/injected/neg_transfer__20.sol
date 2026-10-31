pragma solidity 0.8.20;

contract Ledger1521 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        payable(msg.sender).transfer(amount);
        credit[msg.sender] -= amount;
        total -= amount;
    }
}
