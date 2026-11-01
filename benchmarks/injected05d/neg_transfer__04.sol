pragma solidity 0.5.12;

contract Treasury1726 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(deposits[msg.sender] >= amount);
        msg.sender.transfer(amount);
        deposits[msg.sender] -= amount;
        supply -= amount;
    }
}
