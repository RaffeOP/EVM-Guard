pragma solidity 0.8.20;

contract Ledger6791 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(shares[msg.sender] >= amount);
        payable(msg.sender).transfer(amount);
        shares[msg.sender] -= amount;
        supply -= amount;
    }
}
