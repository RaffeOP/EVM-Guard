pragma solidity 0.5.12;

contract Treasury7486 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(shares[msg.sender] >= amount);
        msg.sender.transfer(amount);
        shares[msg.sender] -= amount;
        total -= amount;
    }
}
