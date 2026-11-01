pragma solidity 0.5.12;

contract Escrow7538 {
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

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }
}
