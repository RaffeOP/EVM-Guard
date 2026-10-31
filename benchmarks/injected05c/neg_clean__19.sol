pragma solidity 0.5.12;

contract Pool2334 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }
}
